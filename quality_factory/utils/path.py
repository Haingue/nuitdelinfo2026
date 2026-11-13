"""
Utilitaires pour la manipulation des chemins
"""

import fnmatch
import os
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Set, Tuple


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


def dir_matches_ignored(name: str, ignored_dirs: Optional[Set[str]] = None) -> bool:
    """Vérifie si un nom de dossier correspond à un dossier ignoré (gère les globs comme *.egg-info)"""
    if ignored_dirs is None:
        ignored_dirs = IGNORED_DIRS
    if name in ignored_dirs:
        return True
    return any(
        fnmatch.fnmatch(name, pat)
        for pat in ignored_dirs
        if "*" in pat or "?" in pat
    )


def walk_pruned(
    root: Path,
    ignored_dirs: Optional[Set[str]] = None,
) -> Iterator[Tuple[Path, List[str], List[str]]]:
    """
    Parcourt l'arborescence comme os.walk mais SANS descendre dans les
    dossiers ignorés (node_modules, .git, target…), contrairement à rglob
    qui parcourt tout puis filtre a posteriori.
    
    Args:
        root: Répertoire racine
        ignored_dirs: Dossiers à ignorer (par défaut: IGNORED_DIRS)
        
    Yields:
        Tuples (dirpath, dirnames, filenames)
    """
    for dirpath, dirnames, filenames in os.walk(root):
        # Élagage en place: os.walk ne descendra pas dans ces dossiers
        dirnames[:] = [d for d in dirnames if not dir_matches_ignored(d, ignored_dirs)]
        yield Path(dirpath), dirnames, filenames


def find_files_with_patterns(
    root: Path,
    patterns: Sequence[str],
    ignored_dirs: Optional[Set[str]] = None,
) -> Dict[str, List[Path]]:
    """
    Trouve les fichiers correspondant à plusieurs patterns en UNE SEULE
    traversée de l'arborescence (avec élagage des dossiers ignorés).
    
    Args:
        root: Répertoire racine
        patterns: Patterns de fichiers (ex: ["*.py", "pom.xml"])
        ignored_dirs: Dossiers à ignorer (par défaut: IGNORED_DIRS)
        
    Returns:
        Dictionnaire pattern -> liste des chemins des fichiers
    """
    results: Dict[str, List[Path]] = {pattern: [] for pattern in patterns}
    for dirpath, _dirnames, filenames in walk_pruned(root, ignored_dirs):
        for filename in filenames:
            for pattern in patterns:
                if fnmatch.fnmatch(filename, pattern):
                    results[pattern].append(dirpath / filename)
    return results


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
    return find_files_with_patterns(root, (pattern,), ignored_dirs)[pattern]


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
