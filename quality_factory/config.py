"""
Configuration centrale pour Quality Factory
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Configuration principale pour l'exécution des tests"""
    
    # Chemins
    workspace: Path = Path.cwd()
    coverage_dir: Path = Path("coverage-artifacts")
    results_file: Path = Path("test-results.json")
    temp_dir: Path = Path("/tmp")
    
    # Versions des outils
    python_version: str = "3.11"
    java_version: str = "21"
    node_version: str = "20"
    
    # Timeout pour les commandes (en secondes)
    command_timeout: int = 300
    
    # Seuil pour considérer qu'un projet a des tests
    min_test_files: int = 1
    
    @classmethod
    def from_env(cls) -> "Config":
        """Crée une config à partir des variables d'environnement"""
        import os
        
        workspace = Path(os.getenv("GITHUB_WORKSPACE", str(Path.cwd())))
        coverage_dir = Path(os.getenv("COVERAGE_OUTPUT_DIR", str(workspace / "coverage-artifacts")))
        results_file = Path(os.getenv("RESULTS_FILE", str(workspace / "test-results.json")))
        temp_dir = Path(os.getenv("RUNNER_TEMP", "/tmp"))
        
        return cls(
            workspace=workspace,
            coverage_dir=coverage_dir,
            results_file=results_file,
            temp_dir=temp_dir,
        )


# Configuration globale
config = Config()
