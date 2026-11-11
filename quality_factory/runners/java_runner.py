"""
Exécuteur de tests Java avec Maven/Gradle et JaCoCo
"""

import subprocess
import xml.etree.ElementTree as ET
import glob
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from ..models import ProjectInfo, TestSuiteResult, TestStatus, BuildTool
from ..utils.command import (
    run_command, 
    command_exists, 
    find_maven_executable, 
    find_gradle_executable
)


def run_java_tests(
    project: ProjectInfo,
    coverage_dir: Path,
    temp_dir: Path,
) -> TestSuiteResult:
    """
    Exécute les tests Java avec Maven ou Gradle et JaCoCo
    
    Args:
        project: Informations sur le projet
        coverage_dir: Dossier de sortie des rapports de couverture
        temp_dir: Dossier temporaire pour les fichiers init
        
    Returns:
        Résultat de la suite de tests
    """
    project_path = project.path
    suite_name = f"Java ({project_path})"
    
    # Créer le dossier de couverture
    coverage_dir.mkdir(parents=True, exist_ok=True)
    
    # Créer le fichier init.gradle pour JaCoCo (si Gradle)
    if project.build_tool == BuildTool.GRADLE:
        init_gradle_path = temp_dir / "jacoco.init.gradle"
        create_jacoco_init_gradle(init_gradle_path)
    
    try:
        if project.build_tool == BuildTool.MAVEN:
            return run_maven_tests(project_path, coverage_dir, suite_name)
        else:
            return run_gradle_tests(project_path, coverage_dir, temp_dir, suite_name)
            
    except Exception as e:
        return TestSuiteResult(
            name=suite_name,
            status=TestStatus.FAILED,
            exit_code=1,
            error=str(e),
        )


def run_maven_tests(
    project_path: Path,
    coverage_dir: Path,
    suite_name: str,
) -> TestSuiteResult:
    """
    Exécute les tests Maven avec JaCoCo
    
    Args:
        project_path: Chemin du projet
        coverage_dir: Dossier de couverture
        suite_name: Nom de la suite
        
    Returns:
        Résultat des tests
    """
    # Vérifier si JaCoCo est déjà configuré
    has_jacoco = check_maven_jacoco(project_path)
    
    # Trouver l'exécutable Maven
    mvn_cmd = find_maven_executable(project_path)
    if not mvn_cmd:
        return TestSuiteResult(
            name=suite_name,
            status=TestStatus.FAILED,
            exit_code=1,
            error="Maven (mvn ou mvnw) non trouvé",
        )
    
    # Exécuter les tests
    if has_jacoco:
        test_cmd = [mvn_cmd, "-B", "-ntp", "verify"]
    else:
        test_cmd = [
            mvn_cmd, "-B", "-ntp",
            "org.jacoco:jacoco-maven-plugin:0.8.14:prepare-agent",
            "verify",
        ]
    
    try:
        result = subprocess.run(
            test_cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=600,
        )
        
        # Générer le rapport JaCoCo
        report_cmd = [
            mvn_cmd if mvn_cmd != "mvn" else mvn_cmd,
            "-B", "-ntp",
            "org.jacoco:jacoco-maven-plugin:0.8.14:report",
        ]
        # Si on utilise mvnw, il faut utiliser le même chemin
        if mvn_cmd.endswith("mvnw"):
            report_cmd[0] = mvn_cmd
        
        report_result = subprocess.run(
            report_cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300,
        )
        
        # Extraire les métriques de test
        test_report = extract_maven_test_results(project_path)
        
        # Copier le rapport de couverture
        copy_jacoco_reports(project_path, coverage_dir)
        
        status = TestStatus.PASSED if result.returncode == 0 and report_result.returncode == 0 else TestStatus.FAILED
        
        return TestSuiteResult(
            name=suite_name,
            status=status,
            exit_code=result.returncode,
            tests_run=test_report.get("tests", 0),
            tests_failed=test_report.get("failures", 0) + test_report.get("errors", 0),
            tests_errors=test_report.get("errors", 0),
            output=result.stdout,
            error=result.stderr if result.returncode != 0 else None,
        )
        
    except subprocess.TimeoutExpired:
        return TestSuiteResult(
            name=suite_name,
            status=TestStatus.FAILED,
            exit_code=-1,
            error="Timeout lors de l'exécution des tests Maven",
        )


def run_gradle_tests(
    project_path: Path,
    coverage_dir: Path,
    temp_dir: Path,
    suite_name: str,
) -> TestSuiteResult:
    """
    Exécute les tests Gradle avec JaCoCo
    
    Args:
        project_path: Chemin du projet
        coverage_dir: Dossier de couverture
        temp_dir: Dossier temporaire
        suite_name: Nom de la suite
        
    Returns:
        Résultat des tests
    """
    # Trouver l'exécutable Gradle
    gradle_cmd = find_gradle_executable(project_path)
    if not gradle_cmd:
        return TestSuiteResult(
            name=suite_name,
            status=TestStatus.FAILED,
            exit_code=1,
            error="Gradle (gradle ou gradlew) non trouvé",
        )
    
    # Chemin du fichier init.gradle
    init_gradle_path = temp_dir / "jacoco.init.gradle"
    create_jacoco_init_gradle(init_gradle_path)
    
    # Commande Gradle
    test_cmd = [
        gradle_cmd,
        "test",
        "--no-daemon",
        f"--init-script={init_gradle_path}",
    ]
    
    try:
        result = subprocess.run(
            test_cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=600,
        )
        
        # Extraire les métriques de test
        test_report = extract_gradle_test_results(project_path)
        
        # Copier le rapport de couverture
        copy_jacoco_reports(project_path, coverage_dir)
        
        status = TestStatus.PASSED if result.returncode == 0 else TestStatus.FAILED
        
        return TestSuiteResult(
            name=suite_name,
            status=status,
            exit_code=result.returncode,
            tests_run=test_report.get("tests", 0),
            tests_failed=test_report.get("failures", 0) + test_report.get("errors", 0),
            tests_errors=test_report.get("errors", 0),
            output=result.stdout,
            error=result.stderr if result.returncode != 0 else None,
        )
        
    except subprocess.TimeoutExpired:
        return TestSuiteResult(
            name=suite_name,
            status=TestStatus.FAILED,
            exit_code=-1,
            error="Timeout lors de l'exécution des tests Gradle",
        )


def check_maven_jacoco(project_path: Path) -> bool:
    """
    Vérifie si JaCoCo est déjà configuré dans le pom.xml
    
    Args:
        project_path: Chemin du projet Maven
        
    Returns:
        True si JaCoCo est configuré
    """
    pom_file = project_path / "pom.xml"
    if not pom_file.exists():
        return False
    
    try:
        root = ET.parse(pom_file).getroot()
        local_name = lambda element: element.tag.rsplit('}', 1)[-1]
        
        for build in root:
            if local_name(build) != 'build':
                continue
            for plugins in build:
                if local_name(plugins) != 'plugins':
                    continue
                for plugin in plugins:
                    if local_name(plugin) != 'plugin':
                        continue
                    artifact = next(
                        (child.text for child in plugin
                         if local_name(child) == 'artifactId'),
                        ''
                    )
                    if artifact != 'jacoco-maven-plugin':
                        continue
                    for execution in plugin.iter():
                        if local_name(execution) == 'goal' and execution.text == 'prepare-agent':
                            return True
        return False
    except (ET.ParseError, OSError):
        return False


def create_jacoco_init_gradle(path: Path) -> None:
    """
    Crée le fichier init.gradle pour JaCoCo
    
    Args:
        path: Chemin où créer le fichier
    """
    content = """allprojects {
    apply plugin: 'jacoco'
    jacoco {
        toolVersion = '0.8.14'
    }
    tasks.withType(Test).configureEach {
        finalizedBy tasks.named('jacocoTestReport')
    }
    tasks.named('jacocoTestReport') {
        reports {
            xml.required = true
        }
    }
}"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def extract_maven_test_results(project_path: Path) -> Dict[str, int]:
    """
    Extrait les résultats des tests Maven depuis les rapports Surefire
    
    Args:
        project_path: Chemin du projet
        
    Returns:
        Dictionnaire avec tests, failures, errors
    """
    patterns = [
        '**/target/surefire-reports/TEST-*.xml',
        '**/target/failsafe-reports/TEST-*.xml',
    ]
    
    tests = 0
    failures = 0
    errors = 0
    
    for pattern in patterns:
        for path in project_path.glob(pattern):
            if not path.exists():
                continue
            try:
                root = ET.parse(path).getroot()
                tests += int(root.attrib.get('tests', 0))
                failures += int(root.attrib.get('failures', 0))
                errors += int(root.attrib.get('errors', 0))
            except (ET.ParseError, OSError, ValueError):
                errors += 1
    
    return {"tests": tests, "failures": failures, "errors": errors}


def extract_gradle_test_results(project_path: Path) -> Dict[str, int]:
    """
    Extrait les résultats des tests Gradle
    
    Args:
        project_path: Chemin du projet
        
    Returns:
        Dictionnaire avec tests, failures, errors
    """
    patterns = [
        '**/build/test-results/test/TEST-*.xml',
    ]
    
    tests = 0
    failures = 0
    errors = 0
    
    for pattern in patterns:
        for path in project_path.glob(pattern):
            if not path.exists():
                continue
            try:
                root = ET.parse(path).getroot()
                tests += int(root.attrib.get('tests', 0))
                failures += int(root.attrib.get('failures', 0))
                errors += int(root.attrib.get('errors', 0))
            except (ET.ParseError, OSError, ValueError):
                errors += 1
    
    return {"tests": tests, "failures": failures, "errors": errors}


def copy_jacoco_reports(project_path: Path, coverage_dir: Path) -> None:
    """
    Copie les rapports JaCoCo vers le dossier de couverture
    
    Args:
        project_path: Chemin du projet
        coverage_dir: Dossier de destination
    """
    patterns = [
        '**/target/site/jacoco/jacoco.xml',
        '**/build/reports/jacoco/test/jacocoTestReport.xml',
    ]
    
    for pattern in patterns:
        for report_path in project_path.glob(pattern):
            if report_path.exists():
                relative = report_path.relative_to(project_path)
                dest = coverage_dir / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(report_path, dest)
                print(f"📄 Rapport JaCoCo copié: {report_path} -> {dest}")
