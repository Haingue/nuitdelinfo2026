"""
Utilitaires pour l'intégration GitHub Actions (workflow commands, fichiers
GITHUB_OUTPUT / GITHUB_ENV / GITHUB_STEP_SUMMARY).

Les fonctions sont sans effet si les variables d'environnement ne sont pas
définies (exécution locale hors CI).
"""

import os
import sys


def _append(env_var: str, text: str) -> None:
    path = os.environ.get(env_var)
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(text)


def set_output(name: str, value) -> None:
    """Écrit une sortie de step (GITHUB_OUTPUT)."""
    _append("GITHUB_OUTPUT", f"{name}={value}\n")


def set_env(name: str, value) -> None:
    """Exporte une variable pour les steps suivants (GITHUB_ENV)."""
    _append("GITHUB_ENV", f"{name}={value}\n")


def append_summary(text: str) -> None:
    """Ajoute du Markdown au résumé de la run (GITHUB_STEP_SUMMARY)."""
    _append("GITHUB_STEP_SUMMARY", text)


def error(message: str) -> None:
    print(f"::error::{message}")
    sys.stdout.flush()


def warning(message: str) -> None:
    print(f"::warning::{message}")
    sys.stdout.flush()


def notice(message: str) -> None:
    print(f"::notice::{message}")
    sys.stdout.flush()
