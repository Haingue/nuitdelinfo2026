"""
Module de détection des projets
"""

from .python import detect_python_projects
from .java import detect_java_projects
from .node import detect_node_projects
from ..models import DetectionResult
from pathlib import Path


def detect_all_projects(workspace: Path) -> DetectionResult:
    """
    Détecte tous les projets (Python, Java, Node) dans le workspace
    
    Args:
        workspace: Répertoire racine de recherche
        
    Returns:
        DetectionResult avec tous les projets détectés
    """
    python_projects = detect_python_projects(workspace)
    java_projects = detect_java_projects(workspace)
    node_packages = detect_node_projects(workspace)
    
    return DetectionResult(
        python_projects=python_projects,
        java_projects=java_projects,
        node_packages=node_packages,
    )
