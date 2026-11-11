#!/usr/bin/env python3
"""
Point d'entrée principal pour Quality Factory

Ce script orchestré la détection et l'exécution des tests
pour les projets Java, Python et Node.js.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from quality_factory.config import Config
from quality_factory.models import DetectionResult, ExecutionReport, TestStatus
from quality_factory.detect import detect_all_projects
from quality_factory.runners.python_runner import run_python_tests
from quality_factory.runners.java_runner import run_java_tests
from quality_factory.runners.node_runner import run_node_tests
from quality_factory.report import generate_report, save_report, print_summary


def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(
        description="Quality Factory - Exécuteur de tests multi-langages"
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Répertoire de travail (par défaut: répertoire courant)",
    )
    parser.add_argument(
        "--coverage-dir",
        type=Path,
        default=None,
        help="Dossier de sortie des rapports de couverture (par défaut: <workspace>/coverage-artifacts)",
    )
    parser.add_argument(
        "--results-file",
        type=Path,
        default=None,
        help="Fichier de sortie du rapport JSON (par défaut: <workspace>/test-results.json)",
    )
    parser.add_argument(
        "--temp-dir",
        type=Path,
        default=Path("/tmp"),
        help="Dossier temporaire (par défaut: /tmp)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mode test: détection uniquement, sans exécution",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mode verbeux",
    )
    
    args = parser.parse_args()
    
    # Configuration
    workspace = args.workspace.resolve()
    coverage_dir = args.coverage_dir or (workspace / "coverage-artifacts")
    results_file = args.results_file or (workspace / "test-results.json")
    temp_dir = args.temp_dir.resolve()
    
    print(f"🔍 Workspace: {workspace}")
    print(f"📁 Coverage dir: {coverage_dir}")
    print(f"📄 Results file: {results_file}")
    print(f"🗃️  Temp dir: {temp_dir}")
    print()
    
    # Changer de répertoire de travail
    os.chdir(workspace)
    
    # Étape 1: Détection des projets
    print("🔎 Détection des projets en cours...")
    detection_result = detect_all_projects(workspace)
    
    print(f"✅ Projets détectés:")
    print(f"   Python: {len(detection_result.python_projects)}")
    print(f"   Java: {len(detection_result.java_projects)}")
    print(f"   Node: {len(detection_result.node_packages)}")
    print()
    
    if args.dry_run:
        print("🧪 Mode dry-run: arrêt après détection")
        for proj in detection_result.python_projects:
            print(f"   - Python: {proj.path}")
        for proj in detection_result.java_projects:
            print(f"   - Java: {proj.path} ({proj.build_tool.value})")
        for proj in detection_result.node_packages:
            print(f"   - Node: {proj.path}")
        return 0
    
    # Étape 2: Exécution des tests
    print("⚙️  Exécution des tests en cours...")
    suite_results = []
    
    # Exécuter les tests Python
    for python_project in detection_result.python_projects:
        if args.verbose:
            print(f"\n🐍 Exécution tests Python: {python_project.path}")
        
        python_key = str(python_project.path).replace("/", "__")
        python_coverage_dir = coverage_dir / "python" / python_key
        
        result = run_python_tests(
            project=python_project,
            coverage_dir=python_coverage_dir,
            temp_dir=temp_dir,
        )
        suite_results.append(result)
        
        if args.verbose:
            print(f"   → {result.status.value} (exit: {result.exit_code})")
    
    # Exécuter les tests Java
    for java_project in detection_result.java_projects:
        if args.verbose:
            print(f"\n☕ Exécution tests Java: {java_project.path}")
        
        result = run_java_tests(
            project=java_project,
            coverage_dir=coverage_dir / "java",
            temp_dir=temp_dir,
        )
        suite_results.append(result)
        
        if args.verbose:
            print(f"   → {result.status.value} (exit: {result.exit_code})")
    
    # Exécuter les tests Node
    for node_project in detection_result.node_packages:
        if args.verbose:
            print(f"\n🚀 Exécution tests Node: {node_project.path}")
        
        node_key = str(node_project.path).replace("/", "__")
        node_coverage_dir = coverage_dir / "node" / node_key
        
        result = run_node_tests(
            project=node_project,
            coverage_dir=node_coverage_dir,
        )
        suite_results.append(result)
        
        if args.verbose:
            print(f"   → {result.status.value} (exit: {result.exit_code})")
    
    # Étape 3: Génération du rapport
    print("\n📊 Génération du rapport...")
    report = generate_report(suite_results, workspace)
    
    # Sauvegarder le rapport
    save_report(report, results_file)
    
    # Afficher le résumé
    print_summary(report)
    
    # Afficher les erreurs éventuelles
    for result in suite_results:
        if result.status == TestStatus.FAILED:
            print(f"\n❌ Erreur dans {result.name}:")
            if result.error:
                print(f"   {result.error}")
            if result.output:
                print(f"   Sortie: {result.output[:200]}...")
    
    # Retourner le code de sortie approprié
    if report.status == TestStatus.FAILED:
        print("\n❌ Au moins une suite de tests a échoué")
        return 1
    elif report.status == TestStatus.NOT_FOUND:
        print("\n⚠️  Aucun test détecté")
        return 0
    else:
        print("\n✅ Tous les tests ont réussi")
        return 0


if __name__ == "__main__":
    sys.exit(main())
