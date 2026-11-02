import io
import json
import unittest
import zipfile
from argparse import Namespace
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import requests

import scoring


class LoggingTests(unittest.TestCase):
    def test_api_logs_show_urls_and_status_without_credentials(self):
        response = Mock(status_code=200)
        response.url = 'https://storage.example/report?signature=secret-signature'
        with patch.object(scoring.requests, 'get', return_value=response), \
                self.assertLogs(scoring.logger, level='INFO') as logs:
            scoring.gh_get('https://api.github.com/repos/owner/repo', 'github-secret')
            scoring.sonar_get('/measures/component', 'sonar-secret', component='owner_repo')
        output = '\n'.join(logs.output)
        self.assertIn('https://api.github.com/repos/owner/repo', output)
        self.assertIn('https://sonarcloud.io/api/measures/component', output)
        self.assertIn('owner_repo', output)
        self.assertIn('HTTP 200', output)
        for secret in ('github-secret', 'sonar-secret', 'secret-signature'):
            self.assertNotIn(secret, output)


class DependencyVulnsTests(unittest.TestCase):
    def setUp(self):
        self.team = scoring.Team('Test', 'owner/repo', 'org', 0)
        self.runs = [
            {'id': 1, 'created_at': '2026-10-30T12:00:00Z', 'head_branch': 'main', 'conclusion': 'success'},
            {'id': 2, 'created_at': '2026-10-30T13:00:00Z', 'head_branch': 'main', 'conclusion': 'failure'},
            {'id': 3, 'created_at': '2026-10-30T14:00:00Z', 'head_branch': 'feature', 'conclusion': 'success'},
        ]

    def fetch(self, report, artifacts=None):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('trivy-report.json', json.dumps(report))
        listing = Mock()
        listing.json.return_value = {'artifacts': artifacts if artifacts is not None
                                     else [{'id': 42, 'name': 'trivy-report',
                                            'expired': False}]}
        download = Mock(content=buffer.getvalue())
        with patch.object(scoring, 'fetch_workflow_runs', return_value=self.runs), \
                patch.object(scoring, 'gh_get', side_effect=[listing, download]) as get:
            counts = scoring.fetch_dependency_vulns(self.team, 'token')
        return counts, get

    def test_counts_latest_main_report_even_when_sonar_failed(self):
        counts, get = self.fetch({'Results': [{'Vulnerabilities': [
            {'Severity': 'CRITICAL'}, {'Severity': 'HIGH'},
            {'Severity': 'HIGH'}, {'Severity': 'LOW'},
        ]}]})
        self.assertEqual(counts, (1, 2))
        self.assertIn('/runs/2/artifacts', get.call_args_list[0].args[0])
        self.assertIn('/artifacts/42/zip', get.call_args_list[1].args[0])

    def test_clean_report(self):
        counts, _ = self.fetch({'Results': [{'Class': 'lang-pkgs', 'Packages': [
            {'Name': 'library', 'Version': '1.0'},
        ]}]})
        self.assertEqual(counts, (0, 0))

    def test_unresolved_versions_are_not_a_clean_scan(self):
        counts, _ = self.fetch({'Results': [{'Class': 'lang-pkgs', 'Packages': [
            {'Name': 'org.springframework.boot:spring-boot-starter-web'},
        ]}]})
        self.assertEqual(counts, (-1, -1))

    def test_missing_and_expired_artifacts(self):
        for artifacts in ([], [{'id': 42, 'name': 'trivy-report', 'expired': True}]):
            with self.subTest(artifacts=artifacts):
                counts, get = self.fetch({'Results': []}, artifacts)
                self.assertEqual(counts, (-1, -1))
                self.assertEqual(get.call_count, 1)

    def test_missing_results(self):
        counts, _ = self.fetch({})
        self.assertEqual(counts, (-1, -1))

    def test_no_runs(self):
        self.runs = []
        counts, get = self.fetch({'Results': []})
        self.assertEqual(counts, (-1, -1))
        get.assert_not_called()

    def test_download_errors(self):
        for response in (Mock(content=b'not a zip'),
                         Mock(raise_for_status=Mock(side_effect=requests.HTTPError('403')))):
            with self.subTest(response=response):
                listing = Mock()
                listing.json.return_value = {'artifacts': [
                    {'id': 42, 'name': 'trivy-report', 'expired': False},
                ]}
                with patch.object(scoring, 'fetch_workflow_runs', return_value=self.runs), \
                        patch.object(scoring, 'gh_get', side_effect=[listing, response]):
                    self.assertEqual(scoring.fetch_dependency_vulns(self.team, 'token'),
                                     (-1, -1))


class TestSuiteResultsTests(unittest.TestCase):
    def setUp(self):
        self.team = scoring.Team('Test', 'owner/repo', 'org', 0)
        self.run = {'id': 8, 'created_at': '2026-10-30T14:00:00Z',
                    'head_branch': 'main', 'conclusion': 'failure'}

    def fetch(self, result, artifacts=None):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('test-results.json', json.dumps(result))
        listing = Mock()
        listing.json.return_value = {'artifacts': artifacts if artifacts is not None
                                     else [{'id': 42, 'name': 'test-results',
                                            'expired': False}]}
        download = Mock(content=buffer.getvalue())
        with patch.object(scoring, 'fetch_workflow_runs', return_value=[self.run]), \
                patch.object(scoring, 'gh_get', side_effect=[listing, download]):
            return scoring.fetch_test_result(self.team, 'token')

    def test_reads_passed_test_artifact(self):
        result = self.fetch({'status': 'passed', 'detected': 2, 'failed': 0,
                             'frameworks': 'Python, Node (web)'})
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['detected'], 2)

    def test_reads_failed_test_artifact(self):
        result = self.fetch({'status': 'failed', 'detected': 1, 'failed': 1,
                             'failed_tests': 3})
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['failed_tests'], 3)

    def test_missing_artifact_is_unavailable(self):
        listing = Mock()
        listing.json.return_value = {'artifacts': []}
        with patch.object(scoring, 'fetch_workflow_runs', return_value=[self.run]), \
                patch.object(scoring, 'gh_get', return_value=listing):
            result = scoring.fetch_test_result(self.team, 'token')
        self.assertEqual(result['status'], 'unavailable')

    def test_sonar_metrics_follow_readme_weights_and_numeric_ratings(self):
        cfg = Namespace(gh_token='token', sonar_token='token', salt='salt',
                        window_start=datetime.now(timezone.utc),
                        history_archive={'Test': [{'qualite': 0, 'total': 0}]})
        measures = {
            'sqale_rating': '1.0',
            'security_rating': '2.0',
            'coverage': '30.0',
            'sqale_index': '120',
            'sqale_debt_ratio': '2.3',
            'code_smells': '7',
        }
        for status in ('passed', 'failed'):
            test_result = {'status': status, 'detected': 1,
                           'failed': 0 if status == 'passed' else 1,
                           'frameworks': 'Python'}
            with self.subTest(status=status), patch.multiple(
                    scoring,
                    check_identity=Mock(return_value={'ok': True}),
                    fetch_quality_measures=Mock(return_value=measures),
                    fetch_gate_current=Mock(return_value=True),
                    fetch_test_result=Mock(return_value=test_result),
                    fetch_dependency_vulns=Mock(return_value=(0, 0)),
                    fetch_scan_history=Mock(return_value=[]),
                    fetch_workflow_runs=Mock(return_value=[]),
                    fetch_commits=Mock(return_value=[])):
                score, details = scoring.score_team(self.team, cfg)
            self.assertEqual(score.quality, 51)
            self.assertEqual(score.pente, 0)
            self.assertEqual(details['quality_breakdown'], {
                'gate': 20,
                'maintainability': 15,
                'maintainability_rating': 'A',
                'security': 6,
                'security_rating': 'B',
                'coverage': 5,
                'coverage_percent': 30.0,
                'technical_debt_minutes': 120.0,
                'technical_debt_ratio_percent': 2.3,
                'code_smells': 7.0,
                'supply_chain': 5,
                'total': 51,
            })

    def test_quality_breakdown_awards_dependency_points_only_for_clean_scan(self):
        quality = scoring.quality_breakdown({
            'sqale_rating': 'A', 'security_rating': 'A', 'coverage': '75',
        }, True, 0, 0)
        self.assertEqual(quality['coverage'], 10)
        self.assertEqual(quality['supply_chain'], 5)
        self.assertEqual(quality['gate'], 20)

        quality = scoring.quality_breakdown({'sqale_rating': '5.0', 'coverage': 'invalid'},
                                            False, 1, 0)
        self.assertEqual(quality['maintainability'], 0)
        self.assertEqual(quality['coverage'], 0)
        self.assertEqual(quality['supply_chain'], 0)

    def test_sonar_rating_rejects_non_integer_values(self):
        self.assertIsNone(scoring.sonar_rating_letter('2.5'))
        self.assertEqual(scoring.sonar_rating_letter('5.0'), 'E')

    def test_quality_fetch_requests_scored_and_technical_debt_metrics(self):
        response = Mock(status_code=200)
        response.json.return_value = {'component': {'measures': []}}
        with patch.object(scoring, 'sonar_get', return_value=response) as get:
            scoring.fetch_quality_measures(self.team, 'token')
        metric_keys = get.call_args.kwargs['metricKeys'].split(',')
        self.assertEqual(set(metric_keys), {
            'security_rating', 'sqale_rating', 'coverage', 'sqale_index',
            'sqale_debt_ratio', 'code_smells',
        })


if __name__ == '__main__':
    unittest.main()