"""
Détection des projets Python
"""

from pathlib import Path
from typing import List, Optional
from ..models import ProjectInfo, LanguageType
from ..utils.path import IGNORED_DIRS, PYTHON_MARKERS, find_files_with_patterns


def detect_python_projects(
    workspace: Path,
    test_files: Optional[List[Path]] = None,
) -> List[ProjectInfo]:
    """
    Détecte les projets Python avec des tests
    
    Un projet Python est identifié par:
    - Présence de fichiers de test (test_*.py ou *_test.py)
    - Présence d'un marqueur de projet Python (pyproject.toml, setup.py, etc.)
    
    Args:
        workspace: Répertoire racine
        test_files: Fichiers de test pré-collectés (évite une nouvelle traversée)
        
    Returns:
        Liste des projets Python détectés
    """
    projects = []
    
    # Trouver tous les fichiers de test Python (une seule traversée si non fournis)
    if test_files is None:
        scan = find_files_with_patterns(workspace, ("test_*.py", "*_test.py"), IGNORED_DIRS)
        test_files = scan["test_*.py"] + scan["*_test.py"]
    
    # Grouper les fichiers de test par racine de projet
    project_roots = set()
    for test_file in test_files:
        # Remonter pour trouver la racine du projet
        current = test_file.parent
        project_root = None
        
        while current != workspace and current != current.parent:
            # Vérifier si ce dossier contient un marqueur Python
            if any((current / marker).exists() for marker in PYTHON_MARKERS):
                project_root = current
                break
            
            # Vérifier s'il y a un requirements.txt
            if any(f.name.startswith("requirements") and f.name.endswith(".txt") 
                   for f in current.iterdir() if f.is_file()):
                project_root = current
                break
            
            current = current.parent
        
        if project_root is None:
            project_root = workspace
        
        project_roots.add(project_root)
    
    # Créer les ProjectInfo
    for root in sorted(project_roots, key=lambda p: str(p)):
        projects.append(ProjectInfo(
            path=root,
            language=LanguageType.PYTHON,
            has_tests=True,
        ))
    
    return projects
