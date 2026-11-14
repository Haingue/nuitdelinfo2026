#!/usr/bin/env python3
"""
Scan qualité SonarCloud pour Quality Factory.

Reproduit le job `sonar` du workflow quality.yml :
1. Vérifie la présence des rapports de couverture téléchargés.
2. Lance sonar-scanner avec le paramétrage imposé (non configurable).
3. Vérifie le Quality Gate (bloquant = Jidoka).
4. Exporte le rapport d'analyse SonarCloud (report.json).

Le token SonarCloud est lu depuis la variable d'environnement SONAR_TOKEN.
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# Paramétrage imposé : pas d'exclusions, de seuils ni de chemins configurables
# par les équipes (identique au workflow historique).
SONAR_EXCLUSIONS = (
    "**/*.min.js,**/vendor/**,**/dist/**,**/node_modules/**,"
    "coverage-artifacts/**,**/dto/**,**/entity/**,**/model/**"
)
SONAR_COVERAGE_EXCLUSIONS = (
    "**/*.spec.*,**/tests/**,coverage-artifacts/**,**/dto/**,**/entity/**,**/model/**"
)
QUALITY_GATE_TIMEOUT = 300  # 5 minutes, comme le timeout du step historique
QUALITY_GATE_POLL_INTERVAL = 5


def check_coverage_reports(coverage_dir: Path) -> None:
    """Liste les rapports de couverture disponibles (avertit si absents)."""
    reports = []
    if coverage_dir.is_dir():
        reports = [
            path for path in coverage_dir.rglob("*")
            if path.is_file() and (path.suffix == ".xml" or path.name == "lcov.info")
        ]
    if reports:
        print("Rapports de couverture téléchargés :")
        for path in reports:
            print(f"  {path}")
    else:
        print("::warning::Aucun rapport de couverture disponible; SonarCloud affichera une couverture nulle.")
    sys.stdout.flush()


def run_scanner(project_key: str, organization: str, host: str, coverage_dir: Path) -> int:
    """Lance sonar-scanner avec le paramétrage imposé. Retourne le code de sortie."""
    command = [
        "sonar-scanner",
        f"-Dsonar.projectKey={project_key}",
        f"-Dsonar.organization={organization}",
        f"-Dsonar.host.url={host}",
        "-Dsonar.sources=.",
        f"-Dsonar.exclusions={SONAR_EXCLUSIONS}",
        f"-Dsonar.coverage.exclusions={SONAR_COVERAGE_EXCLUSIONS}",
        f"-Dsonar.coverage.jacoco.xmlReportPaths={coverage_dir}/java/**/jacoco*.xml",
        f"-Dsonar.python.coverage.reportPaths={coverage_dir}/python/**/coverage.xml",
        f"-Dsonar.javascript.lcov.reportPaths={coverage_dir}/node/**/lcov.info",
        "-Dsonar.python.version=3.11",
    ]
    print(f"⚙️  Lancement du scan: {' '.join(command)}")
    sys.stdout.flush()
    result = subprocess.run(command)
    return result.returncode


def read_scan_metadata(workspace: Path) -> dict:
    """Lit .scannerwork/report-task.txt généré par le scanner."""
    metadata_path = workspace / ".scannerwork" / "report-task.txt"
    if not metadata_path.is_file():
        return {}
    return {
        key.strip(): value.strip()
        for line in metadata_path.read_text(errors="replace").splitlines()
        if "=" in line
        for key, value in [line.split("=", 1)]
    }


def get_json(host: str, token: str, endpoint: str, params: dict) -> dict:
    query = urlencode(params)
    request = Request(f"{host}/api/{endpoint}?{query}")
    credentials = base64.b64encode(f"{token}:".encode()).decode()
    request.add_header("Authorization", f"Basic {credentials}")
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def check_quality_gate(host: str, token: str, metadata: dict) -> bool:
    """
    Vérifie le Quality Gate (bloquant = Jidoka).

    Attend la fin de la tâche d'analyse côté SonarCloud puis interroge le
    statut du gate — même comportement que sonarsource/sonarqube-quality-gate-action.
    Retourne True si le gate est vert.
    """
    task_id = metadata.get("ceTaskId")
    if not task_id:
        print("::error::Impossible de vérifier le Quality Gate: ceTaskId absent des métadonnées du scanner.")
        return False

    print("⏳ Attente de la fin de l'analyse SonarCloud...")
    sys.stdout.flush()
    deadline = time.monotonic() + QUALITY_GATE_TIMEOUT
    analysis_id = None
    while time.monotonic() < deadline:
        try:
            task = get_json(host, token, "ce/task", {"id": task_id})["task"]
        except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as error:
            print(f"::error::Échec de l'interrogation de la tâche d'analyse: {type(error).__name__}")
            return False
        status = task.get("status")
        if status == "SUCCESS":
            analysis_id = task.get("analysisId")
            break
        if status in ("FAILED", "CANCELED"):
            print(f"::error::L'analyse SonarCloud a échoué (statut: {status}).")
            return False
        time.sleep(QUALITY_GATE_POLL_INTERVAL)

    if not analysis_id:
        print(f"::error::Timeout ({QUALITY_GATE_TIMEOUT}s) en attendant la fin de l'analyse SonarCloud.")
        return False

    try:
        project_status = get_json(
            host, token, "qualitygates/project_status", {"analysisId": analysis_id}
        )["projectStatus"]
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as error:
        print(f"::error::Échec de la récupération du Quality Gate: {type(error).__name__}")
        return False

    gate_status = project_status.get("status")
    if gate_status == "OK":
        print("✅ Quality Gate: OK")
        return True

    print(f"::error::Quality Gate: {gate_status}")
    for condition in project_status.get("conditions", []):
        if condition.get("status") == "ERROR":
            print(
                f"::error::  {condition.get('metricKey')}: "
                f"{condition.get('actualValue')} (seuil: {condition.get('errorThreshold')})"
            )
    return False


def export_report(
    host: str,
    token: str,
    repository: str,
    organization: str,
    branch: str,
    metadata: dict,
    output: Path,
) -> None:
    """Exporte le rapport d'analyse SonarCloud (Quality Gate, mesures, issues)."""
    project_key = repository.replace("/", "_")
    report = {
        "project": project_key,
        "repository": repository,
        "organization": organization,
        "branch": branch,
        "dashboard_url": f"{host}/project/overview?id={project_key}&branch={branch}",
        "scan_metadata": metadata,
        "quality_gate": None,
        "measures": None,
        "issues": {"total": 0, "items": [], "truncated": False},
        "errors": [],
    }

    if not metadata:
        report["errors"].append("Scanner metadata not found; no completed upload was confirmed.")

    if token and metadata:
        common = {"organization": organization, "branch": branch}
        for section, endpoint, params in (
            ("quality_gate", "qualitygates/project_status",
             {**common, "projectKey": project_key}),
            ("measures", "measures/component", {
                **common,
                "component": project_key,
                "metricKeys": ",".join((
                    "coverage", "duplicated_lines_density", "sqale_rating",
                    "sqale_index", "sqale_debt_ratio", "code_smells",
                    "security_rating", "reliability_rating", "bugs", "vulnerabilities",
                )),
            }),
        ):
            try:
                report[section] = get_json(host, token, endpoint, params)
            except (HTTPError, URLError, TimeoutError, ValueError) as error:
                report["errors"].append(f"{section}: {type(error).__name__}")

        try:
            page = 1
            page_size = 500
            while page <= 100:
                result = get_json(host, token, "issues/search", {
                    **common,
                    "componentKeys": project_key,
                    "resolved": "false",
                    "ps": page_size,
                    "p": page,
                })
                items = result.get("issues", [])
                report["issues"]["total"] = result.get("total", len(items))
                report["issues"]["items"].extend(items)
                if not items or len(report["issues"]["items"]) >= report["issues"]["total"]:
                    break
                page += 1
            report["issues"]["truncated"] = (
                len(report["issues"]["items"]) < report["issues"]["total"]
            )
        except (HTTPError, URLError, TimeoutError, ValueError) as error:
            report["errors"].append(f"issues: {type(error).__name__}")
    elif not token:
        report["errors"].append("Sonar token unavailable to export step.")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"Rapport SonarCloud écrit: {output} ({len(report['issues']['items'])} issues exportées).")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("\n### Rapport détaillé SonarCloud\n\n")
            summary.write(f"Projet : [{project_key}]({report['dashboard_url']})\n\n")
            summary.write("Téléchargez l'artefact **sonar-analysis-report** de cette exécution pour consulter `report.json` (Quality Gate, mesures et issues).\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Quality Factory - Scan SonarCloud (paramétrage imposé)"
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Répertoire de travail (par défaut: répertoire courant)",
    )
    parser.add_argument(
        "--repository",
        required=True,
        help="Dépôt GitHub (owner/repo) — sert à dériver la clé de projet Sonar",
    )
    parser.add_argument(
        "--organization",
        required=True,
        help="Clé de l'organisation SonarCloud de l'équipe",
    )
    parser.add_argument(
        "--host",
        default="https://sonarcloud.io",
        help="URL du serveur SonarCloud",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Branche analysée (pour l'URL du dashboard et l'export du rapport)",
    )
    parser.add_argument(
        "--coverage-dir",
        type=Path,
        default=None,
        help="Dossier des rapports de couverture (par défaut: <workspace>/coverage-artifacts)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Fichier de sortie du rapport JSON (par défaut: <workspace>/sonar-analysis/report.json)",
    )
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    coverage_dir = args.coverage_dir or Path("coverage-artifacts")
    output = args.output or (workspace / "sonar-analysis" / "report.json")
    host = args.host.rstrip("/")
    token = os.environ.get("SONAR_TOKEN", "")
    project_key = args.repository.replace("/", "_")

    os.chdir(workspace)

    # 1. Rapports de couverture disponibles ?
    check_coverage_reports(workspace / coverage_dir)

    # 2. Scan (paramétrage imposé)
    scanner_exit = run_scanner(project_key, args.organization, host, coverage_dir)
    if scanner_exit != 0:
        print(f"::error::sonar-scanner a échoué (code de sortie {scanner_exit}).")

    metadata = read_scan_metadata(workspace)

    # 3. Quality Gate (bloquant = Jidoka)
    gate_ok = False
    if scanner_exit == 0:
        if token:
            gate_ok = check_quality_gate(host, token, metadata)
        else:
            print("::error::SONAR_TOKEN absent: impossible de vérifier le Quality Gate.")

    # 4. Export du rapport d'analyse (toujours, même en cas d'échec en amont)
    export_report(
        host=host,
        token=token,
        repository=args.repository,
        organization=args.organization,
        branch=args.branch,
        metadata=metadata,
        output=output,
    )

    return 0 if (scanner_exit == 0 and gate_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
