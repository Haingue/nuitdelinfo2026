#!/usr/bin/env python3
"""
Supply chain — audit des dépendances pour Quality Factory.

Reproduit le job `dependances` du workflow quality.yml :
1. Pré-résout le modèle et les dépendances Maven (meilleure couverture Trivy),
   sans bloquer en cas d'échec.
2. Lance Trivy (fs, vuln + secrets, HIGH/CRITICAL, rapport JSON).
3. Extrait les métriques supply chain (sorties `critical`/`high`, résumé).
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from quality_factory.utils.github import append_summary, error, notice, set_output, warning

IGNORED_DIRS = {".git", "target", "node_modules"}


def find_first_pom(workspace: Path) -> Path:
    """Premier pom.xml hors dossiers ignorés (équivalent du find -prune)."""
    for current, directories, files in os.walk(workspace):
        directories[:] = sorted(d for d in directories if d not in IGNORED_DIRS)
        if "pom.xml" in files:
            return Path(current) / "pom.xml"
    return None


def preresolve_maven(workspace: Path) -> None:
    """Pré-résout les dépendances Maven ; les échecs ne sont pas bloquants."""
    pom = find_first_pom(workspace)
    if pom is None:
        return
    project_dir = pom.parent
    goal = "org.apache.maven.plugins:maven-dependency-plugin:3.8.1:go-offline"
    if (project_dir / "mvnw").is_file():
        command = ["bash", "./mvnw", "-B", "-ntp", goal, "-DskipTests"]
    else:
        # Maven est fourni par l'image Quality Factory.
        command = ["mvn", "-B", "-ntp", "-f", "pom.xml", goal, "-DskipTests"]
    print(f"📦 Pré-résolution Maven: {' '.join(command)} (dans {project_dir})")
    sys.stdout.flush()
    result = subprocess.run(command, cwd=project_dir)
    if result.returncode != 0:
        warning("Pré-résolution Maven en échec; le scan Trivy peut être incomplet.")


def run_trivy(workspace: Path, report_path: Path) -> int:
    """Scan Trivy (mêmes options que l'action aquasecurity/trivy-action)."""
    command = [
        "trivy", "fs",
        "--scanners", "vuln,secret",
        "--severity", "HIGH,CRITICAL",
        "--format", "json",
        "--output", str(report_path),
        "--exit-code", "0",
        ".",
    ]
    print(f"🔍 Lancement de Trivy: {' '.join(command)}")
    sys.stdout.flush()
    return subprocess.run(command, cwd=workspace).returncode


def extract_metrics(report_path: Path) -> int:
    """Extrait les métriques supply chain du rapport Trivy."""
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        report = None
    if not isinstance(report, dict) or not isinstance(report.get("Results"), list):
        error("Rapport Trivy absent ou invalide; impossible de confirmer l'état des dépendances.")
        return 1

    results = report["Results"]
    vulnerabilities = [v for r in results for v in (r.get("Vulnerabilities") or [])]
    critical = sum(1 for v in vulnerabilities if v.get("Severity") == "CRITICAL")
    high = sum(1 for v in vulnerabilities if v.get("Severity") == "HIGH")
    packages = sum(len(r.get("Packages") or []) for r in results)
    unresolved = sum(
        1 for r in results if r.get("Class") == "lang-pkgs"
        for p in (r.get("Packages") or []) if not (p.get("Version") or "")
    )
    targets = ", ".join(sorted({r.get("Target") for r in results if r.get("Target")}))
    secrets = sum(len(r.get("Secrets") or []) for r in results)

    set_output("critical", critical)
    set_output("high", high)
    notice(
        f"Trivy: CRIT={critical} HIGH={high}, paquets={packages}, "
        f"versions non résolues={unresolved}, secrets={secrets}; cibles={targets}"
    )
    if unresolved > 0:
        warning(
            f"{unresolved} dépendance(s) sans version; leurs dépendances transitives "
            "ne sont pas couvertes. Le scoring supply chain les traite comme un scan incomplet."
        )
    append_summary(
        "### Résultat Trivy\n"
        f"- Cibles analysées : {targets or 'aucune déclarée'}\n"
        f"- Paquets inventoriés : {packages}\n"
        f"- Vulnérabilités HIGH/CRITICAL : {high}/{critical}\n"
        f"- Versions manquantes : {unresolved}\n"
        f"- Secrets détectés : {secrets}\n"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Quality Factory - Audit supply chain (Trivy)"
    )
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Fichier de sortie du rapport Trivy (par défaut: <workspace>/trivy-report.json)",
    )
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    report_path = args.report or (workspace / "trivy-report.json")
    os.chdir(workspace)

    preresolve_maven(workspace)

    trivy_exit = run_trivy(workspace, report_path)
    if trivy_exit != 0:
        error(f"Trivy a échoué (code de sortie {trivy_exit}).")
        return trivy_exit

    return extract_metrics(report_path)


if __name__ == "__main__":
    sys.exit(main())
