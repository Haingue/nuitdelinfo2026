"""
Exécuteur de tests Python avec pytest et couverture
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from ..models import ProjectInfo, TestSuiteResult, TestStatus
from ..utils.command import run_command, command_exists


def run_python_tests(
    project: ProjectInfo,
    coverage_dir: Path,
    temp_dir: Optional[Path] = None,
) -> TestSuiteResult:
    """
    Exécute les tests Python avec pytest et couverture
    
    Args:
        project: Informations sur le projet
        coverage_dir: Dossier de sortie des rapports de couverture
        temp_dir: Dossier temporaire (optionnel)
        
    Returns:
        Résultat de la suite de tests
    """
    project_path = project.path
    suite_name = f"Python (pytest {project_path})"
    coverage_file = coverage_dir / "coverage.xml"
    
    # Créer le dossier de couverture
    coverage_dir.mkdir(parents=True, exist_ok=True)
    
    # Vérifier que Python est disponible (une seule recherche, mise en cache)
    if command_exists("python3"):
        python_cmd = "python3"
    elif command_exists("python"):
        python_cmd = "python"
    else:
        return TestSuiteResult(
            name=suite_name,
            status=TestStatus.FAILED,
            exit_code=1,
            error="Python non trouvé dans le PATH",
        )
    
    try:
        # Étape 1: Installer les dépendances
        install_result = install_python_dependencies(project_path, python_cmd)
        if install_result != 0:
            return TestSuiteResult(
                name=suite_name,
                status=TestStatus.FAILED,
                exit_code=install_result,
                error=f"Échec de l'installation des dépendances (code: {install_result})",
            )
        
        # Étape 2: Exécuter les tests avec couverture
        test_cmd = [
            python_cmd, "-m", "pytest",
            "-q",
            "--cov",
            f"--cov-report=xml:{coverage_file}",
        ]
        
        result = subprocess.run(
            test_cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300,
        )
        
        # Extraire le nombre de tests échoués
        failed_tests = extract_failed_tests_count(result.stdout, result.stderr)
        tests_run = extract_tests_run_count(result.stdout, result.stderr)
        
        status = TestStatus.PASSED if result.returncode == 0 else TestStatus.FAILED
        
        return TestSuiteResult(
            name=suite_name,
            status=status,
            exit_code=result.returncode,
            tests_run=tests_run,
            tests_failed=failed_tests,
            coverage_file=coverage_file,
            output=result.stdout,
            error=result.stderr if result.returncode != 0 else None,
        )
        
    except subprocess.TimeoutExpired:
        return TestSuiteResult(
            name=suite_name,
            status=TestStatus.FAILED,
            exit_code=-1,
            error="Timeout lors de l'exécution des tests",
        )
    except Exception as e:
        return TestSuiteResult(
            name=suite_name,
            status=TestStatus.FAILED,
            exit_code=1,
            error=str(e),
        )


def install_python_dependencies(project_path: Path, python_cmd: str) -> int:
    """
    Installe les dépendances Python
    
    Args:
        project_path: Chemin du projet
        python_cmd: Commande Python à utiliser
        
    Returns:
        Code de retour (0 = succès)
    """
    # Trouver les fichiers requirements.txt
    requirements_files = sorted(
        f for f in project_path.glob("requirements*.txt") if f.is_file()
    )
    
    # Installer pytest et pytest-cov
    install_cmd = [
        python_cmd, "-m", "pip", "install",
        "--disable-pip-version-check",
        "pytest", "pytest-cov",
    ]
    
    try:
        for req_file in requirements_files:
            result = subprocess.run(
                [python_cmd, "-m", "pip", "install", "--disable-pip-version-check", "-r", str(req_file)],
                cwd=project_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"⚠️  Échec installation {req_file}: {result.stderr}")
                return result.returncode
        
        # Installer les dépendances du projet (si pyproject.toml ou setup.py)
        if (project_path / "pyproject.toml").exists() or \
           (project_path / "setup.py").exists() or \
           (project_path / "setup.cfg").exists():
            result = subprocess.run(
                [python_cmd, "-m", "pip", "install", "--disable-pip-version-check", "-e", "."],
                cwd=project_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"⚠️  Échec installation projet: {result.stderr}")
                return result.returncode
        
        return 0
        
    except Exception as e:
        print(f"❌ Erreur lors de l'installation: {e}")
        return 1


def extract_failed_tests_count(stdout: str, stderr: str) -> int:
    """
    Extrait le nombre de tests échoués depuis la sortie de pytest
    
    Args:
        stdout: Sortie standard
        stderr: Sortie d'erreur
        
    Returns:
        Nombre de tests échoués
    """
    import re
    
    # Chercher dans stdout
    match = re.search(r'(\d+) failed', stdout)
    if match:
        return int(match.group(1))
    
    # Chercher dans stderr
    match = re.search(r'(\d+) failed', stderr)
    if match:
        return int(match.group(1))
    
    return 0


def extract_tests_run_count(stdout: str, stderr: str) -> int:
    """
    Extrait le nombre total de tests exécutés
    
    Args:
        stdout: Sortie standard
        stderr: Sortie d'erreur
        
    Returns:
        Nombre de tests exécutés
    """
    import re
    
    # Chercher dans stdout
    match = re.search(r'(\d+) passed', stdout)
    if match:
        return int(match.group(1))
    
    # Alternative: "ran X tests"
    match = re.search(r'ran (\d+) test', stdout)
    if match:
        return int(match.group(1))
    
    return 0
