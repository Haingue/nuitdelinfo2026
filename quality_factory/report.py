"""
Génération du rapport de tests
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from .models import TestSuiteResult, ExecutionReport, TestStatus


def generate_report(
    suite_results: List[TestSuiteResult],
    workspace: Path,
) -> ExecutionReport:
    """
    Génère un rapport d'exécution complet
    
    Args:
        suite_results: Liste des résultats des suites
        workspace: Répertoire de travail
        
    Returns:
        ExecutionReport complet
    """
    detected = len(suite_results)
    failed = sum(1 for r in suite_results if r.status == TestStatus.FAILED)
    failed_tests = sum(r.tests_failed for r in suite_results)
    frameworks = ", ".join(r.name for r in suite_results)
    
    # Déterminer le statut global
    if detected == 0:
        status = TestStatus.NOT_FOUND
    elif failed > 0:
        status = TestStatus.FAILED
    else:
        status = TestStatus.PASSED
    
    # Convertir les résultats en dictionnaires
    suite_dicts = [r.to_dict() for r in suite_results]
    
    return ExecutionReport(
        status=status,
        detected=detected,
        failed=failed,
        failed_tests=failed_tests,
        frameworks=frameworks,
        suite_results=suite_dicts,
    )


def save_report(report: ExecutionReport, path: Path) -> None:
    """
    Sauvegarde le rapport au format JSON
    
    Args:
        report: Rapport à sauvegarder
        path: Chemin du fichier de sortie
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    
    print(f"✅ Rapport sauvegardé: {path}")


def print_summary(report: ExecutionReport) -> None:
    """
    Affiche un résumé du rapport
    
    Args:
        report: Rapport à afficher
    """
    print(f"\n{'='*60}")
    print("📊 RAPPORT D'EXÉCUTION DES TESTS")
    print(f"{'='*60}")
    print(f"Statut: {report.status.value.upper()}")
    print(f"Suites détectées: {report.detected}")
    print(f"Suites en échec: {report.failed}")
    print(f"Tests en échec: {report.failed_tests}")
    print(f"Frameworks: {report.frameworks}")
    print(f"{'='*60}\n")
    
    # Détails des suites
    for suite in report.suite_results:
        status_icon = "✅" if suite["status"] == "passed" else "❌"
        print(f"{status_icon} {suite['name']} (exit: {suite['exit_code']})")
        if suite.get("tests_run", 0) > 0:
            print(f"   Tests: {suite['tests_run']}, Échecs: {suite['tests_failed']}")
    print()
