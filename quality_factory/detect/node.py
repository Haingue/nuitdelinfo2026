"""
Détection des projets Node.js
"""

import json
from pathlib import Path
from typing import List
from ..models import ProjectInfo, LanguageType
from ..utils.path import IGNORED_DIRS, find_files_with_pattern


def detect_node_projects(workspace: Path) -> List[ProjectInfo]:
    """
    Détecte les projets Node.js avec un script de test
    
    Args:
        workspace: Répertoire racine
        
    Returns:
        Liste des projets Node détectés
    """
    projects = []
    
    # Trouver tous les fichiers package.json
    package_files = find_files_with_pattern(workspace, "package.json", IGNORED_DIRS)
    
    for package_file in package_files:
        # Vérifier si le package.json a un script 'test'
        if has_test_script(package_file):
            # La racine du projet est le dossier parent du package.json
            project_root = package_file.parent
            projects.append(ProjectInfo(
                path=project_root,
                language=LanguageType.NODE,
                has_tests=True,
            ))
    
    return projects


def has_test_script(package_file: Path) -> bool:
    """
    Vérifie si un package.json a un script 'test'
    
    Args:
        package_file: Chemin vers le fichier package.json
        
    Returns:
        True si le script existe
    """
    try:
        with open(package_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return 'scripts' in data and 'test' in data['scripts']
    except (json.JSONDecodeError, OSError):
        return False
