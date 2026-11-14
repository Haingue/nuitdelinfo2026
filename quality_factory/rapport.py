#!/usr/bin/env python3
"""
Rapport d'usine pour Quality Factory.

Reproduit le job `rapport` du workflow quality.yml : écrit dans le résumé de
la run le badge de conformité (statuts des jobs) puis le score officiel du
dernier batch, récupéré depuis data/leaderboard.json du dépôt du challenge.
"""

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).parent.parent))

from quality_factory.utils.github import append_summary


def fetch_team_score(challenge_repo: str, team_repo: str):
    """Retourne l'entrée leaderboard de l'équipe (score numérique), ou None."""
    url = f"https://raw.githubusercontent.com/{challenge_repo}/main/data/leaderboard.json"
    try:
        with urlopen(url, timeout=30) as response:
            leaderboard = json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError):
        return None
    if not isinstance(leaderboard, list):
        return None
    for entry in leaderboard:
        if (
            isinstance(entry, dict)
            and entry.get("repo") == team_repo
            and isinstance(entry.get("score"), (int, float))
            and not isinstance(entry.get("score"), bool)
        ):
            return entry
    return None


def render_score(entry: dict) -> str:
    """Rendu Markdown du score officiel (mêmes champs que l'ancien filtre jq)."""
    def value(data, key, default):
        got = data.get(key)
        return default if got is None else got

    breakdown = entry.get("breakdown") or {}
    eligible = "éligible" if entry.get("eligible") else "non éligible"
    return (
        f"**Score : {entry['score']} points** · Rang : {value(entry, 'rank', 'indisponible')}\n"
        "\n"
        f"Classement : {eligible}\n"
        "\n"
        f"Dernière mise à jour : {value(entry, 'timestamp', 'indisponible')}\n"
        "\n"
        "| Composante | Points |\n"
        "|---|---:|\n"
        f"| Qualité | {value(breakdown, 'qualite', 0)} / 60 |\n"
        f"| Progression Kaizen | {value(breakdown, 'pente', 0)} / 20 |\n"
        f"| Résilience | {value(breakdown, 'resilience', 0)} / 10 |\n"
        f"| Régularité Heijunka | {value(breakdown, 'heijunka', 0)} / 10 |\n"
        f"| Bonus / malus | {value(breakdown, 'bonus_malus', 0)} |\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Quality Factory - Rapport d'usine (résumé de la run)"
    )
    parser.add_argument("--team-name", required=True)
    parser.add_argument("--team-repo", required=True, help="Dépôt GitHub de l'équipe (owner/repo)")
    parser.add_argument("--challenge-repo", required=True, help="Dépôt du challenge (owner/repo)")
    parser.add_argument("--conformite", default="", help="Résultat du job conformite")
    parser.add_argument("--sonar", default="", help="Résultat du job sonar")
    parser.add_argument("--tests", default="", help="Statut du job tests")
    parser.add_argument("--critical", default="", help="Vulnérabilités CRITICAL détectées")
    parser.add_argument("--high", default="", help="Vulnérabilités HIGH détectées")
    parser.add_argument("--commits", default="", help="Nombre de commits du dépôt")
    args = parser.parse_args()

    append_summary(
        f"### 🏭 Rapport d'usine — {args.team_name}\n"
        "\n"
        "| Contrôle | Statut |\n"
        "|---|---|\n"
        f"| Conformité & identité | {args.conformite} |\n"
        f"| Quality Gate SonarCloud | {args.sonar} |\n"
        f"| Tests détectés | {args.tests or 'indisponible'} |\n"
        f"| Vulnérabilités CRITICAL/HIGH détectées | {args.critical or 'indisponible'}/{args.high or 'indisponible'} |\n"
        f"| Commits du dépôt (toutes dates) | {args.commits or 'indisponible'} |\n"
        "\n"
        "Les versions non résolues par Trivy ne permettent pas de conclure à "
        "l'absence de vulnérabilités. Le seuil de 20 commits pour le classement "
        "porte sur la fenêtre du défi.\n"
        "\n"
        "### Score officiel du dernier batch\n"
        "\n"
    )

    entry = fetch_team_score(args.challenge_repo, args.team_repo)
    if entry:
        append_summary(render_score(entry))
    else:
        append_summary(
            "Score indisponible : aucun score publié pour ce dépôt "
            "ou données temporairement inaccessibles.\n"
        )

    append_summary(
        "\n"
        "Le batch est planifié toutes les 15 minutes. Ce score peut ne pas "
        "encore inclure cette exécution.\n"
        "\n"
        "[Suivre les mises à jour du classement](https://haingue.github.io/nuitdelinfo2026/)\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
