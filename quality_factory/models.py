"""
Modèles de données pour Quality Factory
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any


class TestStatus(Enum):
    """Statut d'une suite de tests"""
    PASSED = "passed"
    FAILED = "failed"
    NOT_FOUND = "not_found"
    SKIPPED = "skipped"


class LanguageType(Enum):
    """Type de langage"""
    PYTHON = "python"
    JAVA = "java"
    NODE = "node"


class BuildTool(Enum):
    """Outil de build pour Java"""
    MAVEN = "maven"
    GRADLE = "gradle"


@dataclass
class TestSuiteResult:
    """Résultat d'une suite de tests"""
    name: str
    status: TestStatus
    exit_code: int
    tests_run: int = 0
    tests_failed: int = 0
    tests_errors: int = 0
    coverage_file: Optional[Path] = None
    output: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "exit_code": self.exit_code,
            "tests_run": self.tests_run,
            "tests_failed": self.tests_failed,
            "tests_errors": self.tests_errors,
        }


@dataclass
class ProjectInfo:
    """Informations sur un projet détecté"""
    path: Path
    language: LanguageType
    build_tool: Optional[BuildTool] = None
    has_tests: bool = True
    
    @property
    def key(self) -> str:
        """Clé unique pour identifier le projet"""
        return str(self.path).replace("/", "__").replace(" ", "_")


@dataclass
class DetectionResult:
    """Résultat de la détection des projets"""
    python_projects: List[ProjectInfo] = field(default_factory=list)
    java_projects: List[ProjectInfo] = field(default_factory=list)
    node_packages: List[ProjectInfo] = field(default_factory=list)
    
    @property
    def all_projects(self) -> List[ProjectInfo]:
        return self.python_projects + self.java_projects + self.node_packages
    
    def is_empty(self) -> bool:
        return len(self.all_projects) == 0


@dataclass
class ExecutionReport:
    """Rapport d'exécution complet"""
    status: TestStatus
    detected: int = 0
    failed: int = 0
    failed_tests: int = 0
    frameworks: str = ""
    suite_results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "detected": self.detected,
            "failed": self.failed,
            "failed_tests": self.failed_tests,
            "frameworks": self.frameworks,
            "suites": self.suite_results,
        }
    
    def save(self, path: Path) -> None:
        """Sauvegarde le rapport au format JSON"""
        import json
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"Rapport sauvegardé: {path}")
