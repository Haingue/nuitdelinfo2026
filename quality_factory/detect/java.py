"""
Détection des projets Java (Maven et Gradle)
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple, Set
from ..models import ProjectInfo, LanguageType, BuildTool
from ..utils.path import IGNORED_DIRS, JAVA_MARKERS


def detect_java_projects(workspace: Path) -> List[ProjectInfo]:
    """
    Détecte les projets Java avec des tests
    
    Args:
        workspace: Répertoire racine
        
    Returns:
        Liste des projets Java détectés avec leur type (Maven/Gradle)
    """
    # Trouver tous les fichiers pom.xml
    pom_files = sorted(
        path for path in workspace.rglob("pom.xml")
        if not any(part in IGNORED_DIRS for part in path.parts)
    )
    
    # Trouver les modules agrégés (à exclure)
    aggregated_modules = find_aggregated_modules(pom_files)
    
    # Trouver les répertoires pom (exclure les modules agrégés)
    pom_dirs = set()
    for pom in pom_files:
        pom_dir = pom.parent.resolve()
        if pom_dir not in aggregated_modules:
            pom_dirs.add(pom_dir)
    
    # Trouver les projets Gradle
    gradle_projects = find_gradle_projects(workspace, pom_dirs)
    
    # Combiner et filtrer ceux qui ont des tests
    all_projects = []
    
    # Ajouter les projets Maven
    for pom_dir in sorted(pom_dirs):
        if has_java_tests(pom_dir):
            all_projects.append(ProjectInfo(
                path=pom_dir,
                language=LanguageType.JAVA,
                build_tool=BuildTool.MAVEN,
                has_tests=True,
            ))
    
    # Ajouter les projets Gradle
    for build_dir, _ in gradle_projects:
        if has_java_tests(build_dir):
            all_projects.append(ProjectInfo(
                path=build_dir,
                language=LanguageType.JAVA,
                build_tool=BuildTool.GRADLE,
                has_tests=True,
            ))
    
    return all_projects


def find_aggregated_modules(pom_files: List[Path]) -> Set[Path]:
    """
    Trouve les modules Maven agrégés (modules dans un pom parent)
    
    Args:
        pom_files: Liste des fichiers pom.xml
        
    Returns:
        Ensemble des chemins des modules agrégés
    """
    aggregated = set()
    
    for pom in pom_files:
        try:
            root = ET.parse(pom).getroot()
        except (ET.ParseError, OSError):
            continue
        
        # Trouver les modules
        for element in root.iter():
            # Gérer le namespace XML
            tag = element.tag.rsplit('}', 1)[-1]
            if tag == 'module' and element.text:
                module_dir = (pom.parent / element.text.strip()).resolve()
                if (module_dir / 'pom.xml').is_file():
                    aggregated.add(module_dir)
    
    return aggregated


def find_gradle_projects(workspace: Path, pom_dirs: Set[Path]) -> List[Tuple[Path, str]]:
    """
    Trouve les projets Gradle
    
    Args:
        workspace: Répertoire racine
        pom_dirs: Répertoires Maven (à exclure)
        
    Returns:
        Liste de (build_dir, kind) où kind est 'gradle' ou 'gradle-kts'
    """
    # Trouver les fichiers settings.gradle
    settings_dirs = set()
    for pattern in ['settings.gradle', 'settings.gradle.kts']:
        for path in workspace.rglob(pattern):
            if not any(part in IGNORED_DIRS for part in path.parts):
                settings_dirs.add(path.parent.resolve())
    
    # Trouver les fichiers build.gradle
    gradle_projects = []
    for pattern in ['build.gradle', 'build.gradle.kts']:
        for path in workspace.rglob(pattern):
            if not any(part in IGNORED_DIRS for part in path.parts):
                build_dir = path.parent.resolve()
                
                # Exclure si c'est dans un répertoire Maven
                if build_dir in pom_dirs:
                    continue
                
                # Exclure si c'est un sous-projet d'un settings.gradle
                if any(parent in settings_dirs for parent in build_dir.parents):
                    continue
                
                kind = 'gradle'
                if pattern == 'build.gradle.kts':
                    kind = 'gradle-kts'
                
                gradle_projects.append((build_dir, kind))
    
    return gradle_projects


def has_java_tests(directory: Path) -> bool:
    """
    Vérifie si un répertoire contient des tests Java
    
    Args:
        directory: Répertoire à vérifier
        
    Returns:
        True si des tests sont trouvés
    """
    for path in directory.rglob('*'):
        if not path.is_file():
            continue
        
        # Ignorer les dossiers système
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        
        # Vérifier si c'est un fichier de test
        if path.name.endswith(('Test.java', 'Tests.java', 'Test.kt', 'Tests.kt')):
            return True
        
        # Vérifier la structure src/test
        relative_parts = path.relative_to(directory).parts
        if len(relative_parts) >= 2:
            for i in range(len(relative_parts) - 1):
                if relative_parts[i] == 'src' and relative_parts[i + 1] == 'test':
                    return True
    
    return False
