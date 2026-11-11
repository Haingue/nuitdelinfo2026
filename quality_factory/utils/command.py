"""
Utilitaires pour exécuter des commandes système
"""

import os
import glob
import subprocess
import shlex
import sys
import threading
from collections import deque
from pathlib import Path
from typing import Optional, Tuple, Callable


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
    live_output: bool = False,
    live_prefix: str = "",
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
        live_output: Si True, affiche la sortie en temps réel
        live_prefix: Préfixe à ajouter à chaque ligne en mode live
        
    Returns:
        Tuple (exit_code, stdout, stderr)
    """
    if live_output:
        return run_command_live(
            command,
            cwd=cwd,
            timeout=timeout,
            shell=shell,
            env=env,
            prefix=live_prefix,
        )
    
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
    
    # Chercher dans les chemins courants de nvm
    nvm_paths = [
        "/usr/local/nvm/versions/node/v20.20.2/bin/node",
        "/usr/local/nvm/versions/node/*/bin/node",
    ]
    
    for pattern in nvm_paths:
        expanded = os.path.expanduser(pattern)
        matches = glob.glob(expanded)
        if matches:
            return matches[0]
    
    return None


def find_pnpm_executable() -> Optional[str]:
    if command_exists("pnpm"):
        return "pnpm"

    # Chercher dans les chemins courants (nvm, pnpm-global, etc.)
    pnpm_paths = [
        "/usr/local/nvm/versions/node/v20.20.2/bin/pnpm",
        "/usr/local/bin/pnpm"
    ]

    for path in pnpm_paths:
        expanded = os.path.expanduser(path)
        if os.path.exists(expanded):
            return expanded

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


# Buffer global pour les logs en temps réel (optionnel, pour l'affichage dynamique)
class LiveOutputBuffer:
    """Buffer circulaire pour stocker les dernières lignes de sortie"""
    
    def __init__(self, max_lines: int = 20):
        self.max_lines = max_lines
        self.lines = deque(maxlen=max_lines)
        self.lock = threading.Lock()
        
    def add_line(self, line: str):
        """Ajoute une ligne au buffer"""
        with self.lock:
            self.lines.append(line)
    
    def get_lines(self) -> list:
        """Récupère toutes les lignes"""
        with self.lock:
            return list(self.lines)
    
    def display(self, prefix: str = ""):
        """Affiche le buffer (20 dernières lignes)"""
        lines = self.get_lines()
        if not lines:
            return
        
        # Effacer les lignes précédentes si on réaffiche
        # (cette partie dépend du terminal, pour l'instant on affiche juste)
        for line in lines:
            if prefix:
                print(f"{prefix} {line}", end='')
            else:
                print(line, end='')
        sys.stdout.flush()


# Buffer global pour la sortie live (optionnel)
_live_output_buffer = LiveOutputBuffer(max_lines=20)


def get_live_output_buffer() -> LiveOutputBuffer:
    """Récupère le buffer global de sortie live"""
    return _live_output_buffer


def run_command_live(
    command: str,
    cwd: Optional[Path] = None,
    timeout: Optional[int] = None,
    shell: bool = False,
    env: Optional[dict] = None,
    buffer: Optional[LiveOutputBuffer] = None,
    prefix: str = "",
) -> Tuple[int, str, str]:
    """
    Exécute une commande et affiche la sortie en temps réel.
    
    Args:
        command: Commande à exécuter
        cwd: Répertoire de travail
        timeout: Timeout en secondes
        shell: Si True, utilise shell=True
        env: Variables d'environnement supplémentaires
        buffer: Buffer optionnel pour stocker la sortie (par défaut: buffer global)
        prefix: Préfixe à ajouter à chaque ligne
        
    Returns:
        Tuple (exit_code, stdout, stderr)
    """
    use_buffer = buffer or _live_output_buffer
    
    try:
        # Préparer la commande
        if not shell:
            cmd_list = shlex.split(command)
        else:
            cmd_list = command
        
        # Lancer le processus
        process = subprocess.Popen(
            cmd_list,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=shell,
            env=env,
            bufsize=1,
            universal_newlines=True,
        )
        
        # Lire la sortie ligne par ligne
        stdout_lines = []
        full_output = ""
        
        def read_stream():
            nonlocal full_output
            try:
                for line in process.stdout:
                    if line:
                        full_output += line
                        stdout_lines.append(line)
                        if use_buffer:
                            use_buffer.add_line(line)
                        # Afficher la ligne en temps réel
                        if prefix:
                            print(f"{prefix}{line}", end='')
                        else:
                            print(line, end='')
                        sys.stdout.flush()
            except Exception:
                pass
        
        # Lire dans un thread pour éviter les blocages
        reader_thread = threading.Thread(target=read_stream, daemon=True)
        reader_thread.start()
        
        # Attendre la fin du processus ou le timeout
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            reader_thread.join(timeout=1)
            raise CommandError(
                f"Commande timeout après {timeout}s: {command}",
                exit_code=-1,
                stdout=full_output,
                stderr="",
            )
        
        reader_thread.join(timeout=1)
        
        return process.returncode, full_output, ""
        
    except Exception as e:
        raise CommandError(
            f"Erreur lors de l'exécution: {command} - {str(e)}",
            exit_code=-1,
        )


def display_live_logs_block(buffer: Optional[LiveOutputBuffer] = None, title: str = "📜 Logs"):
    """
    Affiche un bloc dynamique avec les 20 dernières lignes de logs.
    
    Args:
        buffer: Buffer à afficher (par défaut: buffer global)
        title: Titre du bloc
    """
    use_buffer = buffer or _live_output_buffer
    lines = use_buffer.get_lines()
    
    if not lines:
        print(f"{title}: (aucun log)")
        return
    
    # Afficher le bloc
    print()
    print("=" * 60)
    print(f"{title} - Dernières {len(lines)} lignes")
    print("=" * 60)
    
    for line in lines:
        print(line, end='')
    
    print("=" * 60)
    sys.stdout.flush()


def run_command_with_dynamic_output(
    command: str,
    cwd: Optional[Path] = None,
    timeout: Optional[int] = None,
    shell: bool = False,
    env: Optional[dict] = None,
    prefix: str = "",
    success_message: str = "✅ Succès",
    failure_message: str = "❌ Échec",
) -> Tuple[int, str, str]:
    """
    Exécute une commande avec affichage en temps réel.
    - Affiche les logs ligne par ligne pendant l'exécution
    - Si succès (exit_code=0) : affiche seulement success_message, pas de bloc récapitulatif
    - Si échec : affiche le bloc récapitulatif avec les 20 dernières lignes + failure_message
    
    Args:
        command: Commande à exécuter
        cwd: Répertoire de travail
        timeout: Timeout en secondes
        shell: Si True, utilise shell=True
        env: Variables d'environnement supplémentaires
        prefix: Préfixe à ajouter à chaque ligne
        success_message: Message à afficher en cas de succès
        failure_message: Message à afficher en cas d'échec
        
    Returns:
        Tuple (exit_code, stdout, stderr)
    """
    # Créer un buffer local pour cette commande
    buffer = LiveOutputBuffer(max_lines=20)
    
    try:
        # Exécuter avec sortie live et stockage dans le buffer
        exit_code, stdout, stderr = run_command_live(
            command,
            cwd=cwd,
            timeout=timeout,
            shell=shell,
            env=env,
            buffer=buffer,
            prefix=prefix,
        )
        
        # À la fin de la commande
        if exit_code == 0:
            # Succès : ne pas afficher de bloc, juste un message simple
            print(f"{prefix}{success_message}")
            sys.stdout.flush()
        else:
            # Échec : afficher le bloc récapitulatif
            print()  # Saut de ligne avant le bloc
            print("=" * 60)
            print(f"{prefix}{failure_message} - Dernières 20 lignes:")
            print("=" * 60)
            for line in buffer.get_lines():
                print(f"{prefix}{line}", end='')
            print("=" * 60)
            sys.stdout.flush()
        
        return exit_code, stdout, stderr
        
    except CommandError as e:
        # En cas d'exception (timeout, etc.)
        print()
        print("=" * 60)
        print(f"{prefix}{failure_message} - Erreur: {e.message}")
        print("=" * 60)
        for line in buffer.get_lines():
            print(f"{prefix}{line}", end='')
        print("=" * 60)
        sys.stdout.flush()
        return e.exit_code, e.stdout, e.stderr
