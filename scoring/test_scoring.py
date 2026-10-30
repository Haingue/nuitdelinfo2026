import io
import json
import unittest
import zipfile
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
            {'id': 1, 'created_at': '2026-10-30T12:00:00Z',
             'head_branch': 'main', 'conclusion': 'success'},
            {'id': 2, 'created_at': '2026-10-30T13:00:00Z',
             'head_branch': 'main', 'conclusion': 'failure'},
            {'id': 3, 'created_at': '2026-10-30T14:00:00Z',
             'head_branch': 'feature', 'conclusion': 'success'},
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


if __name__ == '__main__':
    unittest.main()