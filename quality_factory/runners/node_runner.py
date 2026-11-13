"""
Exécuteur de tests Node.js avec npm, yarn, pnpm et couverture LCOV
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from ..models import ProjectInfo, TestSuiteResult, TestStatus
from ..utils.command import (
    run_command, 
    command_exists,
    find_pnpm_executable,
    find_npm_executable,
    find_yarn_executable,
)


def run_node_tests(
    project: ProjectInfo,
    coverage_dir: Path,
) -> TestSuiteResult:
    """
    Exécute les tests Node.js
    
    Args:
        project: Informations sur le projet
        coverage_dir: Dossier de sortie des rapports de couverture
        
    Returns:
        Résultat de la suite de tests
    """
    project_path = project.path
    suite_name = f"Node ({project_path})"
    
    # Créer le dossier de couverture pour ce package
    package_key = str(project_path).replace("/", "__")
    package_coverage_dir = coverage_dir / package_key
    package_coverage_dir.mkdir(parents=True, exist_ok=True)
    
    # Déterminer le gestionnaire de paquets
    package_manager = detect_package_manager(project_path)
    if not package_manager:
        return TestSuiteResult(
            name=suite_name,
            status=TestStatus.FAILED,
            exit_code=1,
            error="Aucun gestionnaire de paquets trouvé (npm, yarn, pnpm)",
        )
    
    try:
        # Étape 1: Installer les dépendances
        install_result = install_node_dependencies(project_path, package_manager)
        if install_result != 0:
            return TestSuiteResult(
                name=suite_name,
                status=TestStatus.FAILED,
                exit_code=install_result,
                error=f"Échec de l'installation des dépendances",
            )
        
        # Étape 2: Vérifier si Vitest est installé
        has_vitest = check_vitest_installed(project_path)
        
        if has_vitest:
            # Exécuter avec couverture Vitest
            coverage_provider = find_vitest_coverage_provider(project_path)
            if coverage_provider:
                return run_vitest_with_coverage(
                    project_path, 
                    package_manager, 
                    package_coverage_dir,
                    coverage_provider,
                    suite_name
                )
            else:
                print("⚠️  Vitest détecté mais aucun provider de couverture installé")
                return run_node_test_script(project_path, package_manager, suite_name)
        else:
            # Exécuter sans couverture
            return run_node_test_script(project_path, package_manager, suite_name)
            
    except Exception as e:
        return TestSuiteResult(
            name=suite_name,
            status=TestStatus.FAILED,
            exit_code=1,
            error=str(e),
        )


def detect_package_manager(project_path: Path) -> Optional[str]:
    """
    Détecte le gestionnaire de paquets utilisé
    
    Args:
        project_path: Chemin du projet
        
    Returns:
        Nom du gestionnaire (pnpm, yarn, npm) ou None
    """
    # Ordre de priorité: pnpm > yarn > npm
    if (project_path / "pnpm-lock.yaml").exists():
        return find_pnpm_executable() or "pnpm"
    if (project_path / "yarn.lock").exists():
        return find_yarn_executable() or "yarn"
    if (project_path / "package-lock.json").exists():
        return find_npm_executable() or "npm"
    return find_npm_executable() or find_yarn_executable() or find_pnpm_executable()


def install_node_dependencies(project_path: Path, package_manager: str) -> int:
    """
    Installe les dépendances Node.js
    
    Args:
        project_path: Chemin du projet
        package_manager: Gestionnaire de paquets
        
    Returns:
        Code de retour (0 = succès)
    """
    try:
        if package_manager == "pnpm":
            result = subprocess.run(
                ["pnpm", "install", "--frozen-lockfile"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300,
            )
        elif package_manager == "yarn":
            result = subprocess.run(
                ["yarn", "install", "--frozen-lockfile"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300,
            )
        else:  # npm
            result = subprocess.run(
                ["npm", "ci"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300,
            )
        
        if result.returncode != 0:
            stderr_tail = "\n".join((result.stderr or "").strip().splitlines()[-10:])
            if stderr_tail:
                print(f"❌ Échec de l'installation des dépendances Node:\n{stderr_tail}")
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print("⏰ Timeout lors de l'installation des dépendances Node")
        return -1
    except Exception as e:
        print(f"❌ Erreur lors de l'installation: {e}")
        return 1


def check_vitest_installed(project_path: Path) -> bool:
    """
    Vérifie si Vitest est installé dans le projet
    
    Args:
        project_path: Chemin du projet
        
    Returns:
        True si Vitest est installé
    """
    try:
        # Vérifier dans package.json
        package_file = project_path / "package.json"
        if package_file.exists():
            with open(package_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            dev_deps = data.get("devDependencies", {})
            deps = data.get("dependencies", {})
            all_deps = {**dev_deps, **deps}
            
            if "vitest" in all_deps:
                return True
        
        return False
    except Exception:
        return False


def find_vitest_coverage_provider(project_path: Path) -> Optional[str]:
    """
    Trouve le provider de couverture pour Vitest
    
    Args:
        project_path: Chemin du projet
        
    Returns:
        Nom du provider (v8 ou istanbul) ou None
    """
    try:
        package_file = project_path / "package.json"
        if package_file.exists():
            with open(package_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            all_deps = {}
            all_deps.update(data.get("dependencies", {}))
            all_deps.update(data.get("devDependencies", {}))
            
            if "@vitest/coverage-v8" in all_deps:
                return "v8"
            if "@vitest/coverage-istanbul" in all_deps:
                return "istanbul"
        
        return None
    except Exception:
        return None


def run_vitest_with_coverage(
    project_path: Path,
    package_manager: str,
    coverage_dir: Path,
    coverage_provider: str,
    suite_name: str,
) -> TestSuiteResult:
    """
    Exécute Vitest avec couverture
    
    Args:
        project_path: Chemin du projet
        package_manager: Gestionnaire de paquets
        coverage_dir: Dossier de couverture
        coverage_provider: Provider de couverture (v8 ou istanbul)
        suite_name: Nom de la suite
        
    Returns:
        Résultat des tests
    """
    # Construire la commande
    if package_manager == "pnpm":
        base_cmd = ["pnpm", "test", "--"]
    elif package_manager == "yarn":
        base_cmd = ["yarn", "test"]
    else:
        base_cmd = ["npm", "test", "--"]
    
    coverage_args = [
        f"--coverage",
        f"--coverage.provider={coverage_provider}",
        f"--coverage.reporter=lcov",
        f"--coverage.reportOnFailure",
        f"--coverage.reportsDirectory={coverage_dir}",
    ]
    
    cmd = base_cmd + coverage_args
    
    try:
        # Hériter de l'environnement (PATH…) en ajoutant CI=true
        env = {**os.environ, "CI": "true"}
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )
        
        # Extraire les métriques de test
        test_report = extract_vitest_results(result.stdout, result.stderr)
        
        status = TestStatus.PASSED if result.returncode == 0 else TestStatus.FAILED
        
        return TestSuiteResult(
            name=suite_name,
            status=status,
            exit_code=result.returncode,
            tests_run=test_report.get("tests", 0),
            tests_failed=test_report.get("failed", 0),
            tests_errors=0,
            coverage_file=coverage_dir / "lcov.info",
            output=result.stdout,
            error=result.stderr if result.returncode != 0 else None,
        )
        
    except subprocess.TimeoutExpired:
        return TestSuiteResult(
            name=suite_name,
            status=TestStatus.FAILED,
            exit_code=-1,
            error="Timeout lors de l'exécution des tests Vitest",
        )


def run_node_test_script(
    project_path: Path,
    package_manager: str,
    suite_name: str,
) -> TestSuiteResult:
    """
    Exécute le script de test Node sans couverture
    
    Args:
        project_path: Chemin du projet
        package_manager: Gestionnaire de paquets
        suite_name: Nom de la suite
        
    Returns:
        Résultat des tests
    """
    if package_manager == "pnpm":
        cmd = ["pnpm", "test"]
    elif package_manager == "yarn":
        cmd = ["yarn", "test"]
    else:
        cmd = ["npm", "test"]
    
    try:
        # Hériter de l'environnement (PATH…) en ajoutant CI=true
        env = {**os.environ, "CI": "true"}
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )
        
        status = TestStatus.PASSED if result.returncode == 0 else TestStatus.FAILED
        
        return TestSuiteResult(
            name=suite_name,
            status=status,
            exit_code=result.returncode,
            tests_run=0,
            tests_failed=0,
            tests_errors=0,
            output=result.stdout,
            error=result.stderr if result.returncode != 0 else None,
        )
        
    except subprocess.TimeoutExpired:
        return TestSuiteResult(
            name=suite_name,
            status=TestStatus.FAILED,
            exit_code=-1,
            error="Timeout lors de l'exécution des tests Node",
        )


def extract_vitest_results(stdout: str, stderr: str) -> Dict[str, int]:
    """
    Extrait les résultats des tests Vitest
    
    Args:
        stdout: Sortie standard
        stderr: Sortie d'erreur
        
    Returns:
        Dictionnaire avec tests et failed
    """
    import re
    
    # Chercher le résumé Vitest
    # Format: "Test Files  X passed (Y) | Z failed"
    match = re.search(r'Test Files\s+(\d+)\s+passed.*?\|\s*(\d+)\s+failed', stdout)
    if match:
        return {"tests": int(match.group(1)), "failed": int(match.group(2))}
    
    # Alternative
    match = re.search(r'(\d+)\s+passed', stdout)
    if match:
        return {"tests": int(match.group(1)), "failed": 0}
    
    return {"tests": 0, "failed": 0}
