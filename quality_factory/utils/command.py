"""
Utilitaires pour exécuter des commandes système
"""

import subprocess
import shlex
from pathlib import Path
from typing import Optional, Tuple


class CommandError(Exception):
    """Erreur lors de l'exécution d'une commande"""
    def __init__(self, message: str, exit_code: int, stdout: str = "", stderr: str = ""):
        super().__init__(message)
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


def run_command(
    command: str,
    cwd: Optional[Path] = None,
    timeout: Optional[int] = None,
    capture_output: bool = True,
    shell: bool = False,
    env: Optional[dict] = None,
) -> Tuple[int, str, str]:
    """
    Exécute une commande et retourne (exit_code, stdout, stderr)
    
    Args:
        command: Commande à exécuter
        cwd: Répertoire de travail
        timeout: Timeout en secondes
        capture_output: Si True, capture stdout/stderr
        shell: Si True, utilise shell=True
        env: Variables d'environnement supplémentaires
        
    Returns:
        Tuple (exit_code, stdout, stderr)
    """
    try:
        # Si shell=False, on split la commande
        if not shell:
            cmd_list = shlex.split(command)
        else:
            cmd_list = command
            
        result = subprocess.run(
            cmd_list,
            cwd=cwd,
            timeout=timeout,
            capture_output=capture_output,
            text=True,
            shell=shell,
            env=env,
        )
        
        stdout = result.stdout if capture_output else ""
        stderr = result.stderr if capture_output else ""
        
        return result.returncode, stdout, stderr
        
    except subprocess.TimeoutExpired as e:
        raise CommandError(
            f"Commande timeout après {timeout}s: {command}",
            exit_code=-1,
            stdout=e.stdout.decode() if e.stdout else "",
            stderr=e.stderr.decode() if e.stderr else "",
        )
    except Exception as e:
        raise CommandError(
            f"Erreur lors de l'exécution: {command} - {str(e)}",
            exit_code=-1,
        )


def command_exists(command: str) -> bool:
    """Vérifie si une commande existe dans le PATH"""
    import shutil
    return shutil.which(command) is not None


def find_java_executable() -> Optional[str]:
    """Trouve l'exécutable Java"""
    candidates = ["java", "java21", "java-21", "/usr/lib/jvm/java-21-bin/bin/java"]
    for cmd in candidates:
        if command_exists(cmd):
            return cmd
    return None


def find_maven_executable(project_path: Path) -> Optional[str]:
    """Trouve l'exécutable Maven (mvnw ou mvn)"""
    mvnw = project_path / "mvnw"
    if mvnw.exists():
        return str(mvnw)
    if command_exists("mvn"):
        return "mvn"
    return None


def find_gradle_executable(project_path: Path) -> Optional[str]:
    """Trouve l'exécutable Gradle (gradlew ou gradle)"""
    gradlew = project_path / "gradlew"
    if gradlew.exists():
        return str(gradlew)
    if command_exists("gradle"):
        return "gradle"
    return None


def find_node_executable() -> Optional[str]:
    """Trouve l'exécutable Node"""
    candidates = ["node", "node20"]
    for cmd in candidates:
        if command_exists(cmd):
            return cmd
    return None


def find_pnpm_executable() -> Optional[str]:
    """Trouve l'exécutable pnpm"""
    if command_exists("pnpm"):
        return "pnpm"
    return None


def find_npm_executable() -> Optional[str]:
    """Trouve l'exécutable npm"""
    if command_exists("npm"):
        return "npm"
    return None


def find_yarn_executable() -> Optional[str]:
    """Trouve l'exécutable yarn"""
    if command_exists("yarn"):
        return "yarn"
    return None
