"""
Utilitaires pour la manipulation des chemins
"""

from pathlib import Path
from typing import Set, List, Optional


# Dossiers à ignorer lors de la détection
IGNORED_DIRS: Set[str] = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "build",
    "dist",
    "target",
    ".mvn",
    ".gradle",
    ".idea",
    ".vscode",
    "*.egg-info",
}

# Fichiers marqueurs pour les projets Python
PYTHON_MARKERS: Set[str] = {
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "Pipfile",
    "poetry.lock",
    "uv.lock",
    "requirements.txt",
    "requirements-dev.txt",
}

# Fichiers marqueurs pour les projets Java
JAVA_MARKERS: Set[str] = {
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
}

# Fichiers marqueurs pour les projets Node
NODE_MARKERS: Set[str] = {
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "package-lock.json",
}


def is_ignored_dir(name: str) -> bool:
    """Vérifie si un dossier doit être ignoré"""
    return name in IGNORED_DIRS or name.startswith(".")


def find_files_with_pattern(root: Path, pattern: str, ignored_dirs: Optional[Set[str]] = None) -> List[Path]:
    """
    Trouve tous les fichiers correspondant à un pattern
    
    Args:
        root: Répertoire racine
        pattern: Pattern de fichier (ex: "*.py")
        ignored_dirs: Dossiers à ignorer (par défaut: IGNORED_DIRS)
        
    Returns:
        Liste des chemins des fichiers
    """
    if ignored_dirs is None:
        ignored_dirs = IGNORED_DIRS
    
    result = []
    for path in root.rglob(pattern):
        if path.is_file():
            # Vérifier que le chemin ne passe pas par un dossier ignoré
            if not any(part in ignored_dirs for part in path.parts):
                result.append(path)
    return result


def find_project_roots(root: Path, markers: Set[str], ignored_dirs: Optional[Set[str]] = None) -> Set[Path]:
    """
    Trouve les racines de projet en cherchant des fichiers marqueurs
    
    Args:
        root: Répertoire racine
        markers: Ensemble de fichiers marqueurs
        ignored_dirs: Dossiers à ignorer
        
    Returns:
        Ensemble des chemins des racines de projet
    """
    if ignored_dirs is None:
        ignored_dirs = IGNORED_DIRS
    
    project_roots = set()
    
    # Trouver tous les fichiers marqueurs
    for marker in markers:
        for marker_path in root.rglob(marker):
            if marker_path.is_file():
                # Remonter jusqu'à la racine du projet
                project_root = find_project_root(marker_path.parent, markers, ignored_dirs)
                if project_root:
                    project_roots.add(project_root)
    
    return project_roots


def find_project_root(start_path: Path, markers: Set[str], ignored_dirs: Set[str]) -> Optional[Path]:
    """
    Remonte dans l'arborescence pour trouver la racine du projet
    
    Args:
        start_path: Chemin de départ
        markers: Fichiers marqueurs
        ignored_dirs: Dossiers à ignorer
        
    Returns:
        Chemin de la racine du projet ou None
    """
    current = start_path
    
    while current != current.parent:
        # Vérifier si ce dossier contient un marqueur
        if any((current / marker).exists() for marker in markers):
            return current
        
        # Si on trouve un dossier ignoré, on s'arrête
        if current.name in ignored_dirs:
            return None
            
        current = current.parent
    
    return current


def relative_to_workspace(path: Path, workspace: Path) -> Path:
    """Retourne le chemin relatif au workspace"""
    try:
        return path.relative_to(workspace)
    except ValueError:
        return path


def sanitize_key(path: str) -> str:
    """Nettoie un chemin pour en faire une clé valide"""
    return path.replace("/", "__").replace(" ", "_").replace(".", "_")
