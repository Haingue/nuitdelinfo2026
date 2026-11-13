"""
Module de détection des projets
"""

from .python import detect_python_projects
from .java import detect_java_projects, JAVA_SCAN_PATTERNS
from .node import detect_node_projects
from ..models import DetectionResult
from ..utils.path import find_files_with_patterns
from pathlib import Path


# Tous les patterns nécessaires à la détection, collectés en une seule traversée
SCAN_PATTERNS = ("test_*.py", "*_test.py", "package.json") + JAVA_SCAN_PATTERNS


def detect_all_projects(workspace: Path) -> DetectionResult:
    """
    Détecte tous les projets (Python, Java, Node) dans le workspace
    
    Args:
        workspace: Répertoire racine de recherche
        
    Returns:
        DetectionResult avec tous les projets détectés
    """
    # Une seule traversée du workspace pour tous les langages
    scan = find_files_with_patterns(workspace, SCAN_PATTERNS)
    
    python_projects = detect_python_projects(
        workspace,
        test_files=scan["test_*.py"] + scan["*_test.py"],
    )
    java_projects = detect_java_projects(workspace, marker_files=scan)
    node_packages = detect_node_projects(workspace, package_files=scan["package.json"])
    
    return DetectionResult(
        python_projects=python_projects,
        java_projects=java_projects,
        node_packages=node_packages,
    )
