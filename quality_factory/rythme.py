#!/usr/bin/env python3
"""
Heijunka — régularité des commits pour Quality Factory.

Reproduit le job `rythme` du workflow quality.yml :
1. Contrôle le nombre minimum de commits (sortie `commits`).
2. Exporte l'historique horodaté (artefact/commit-history.csv) — le calcul
   d'entropie horaire est fait côté batch (leaderboard), pas en CI.
"""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from quality_factory.utils.github import error, set_output, warning

MIN_COMMITS = 20


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Quality Factory - Heijunka (régularité des commits)"
    )
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    args = parser.parse_args()
    workspace = args.workspace.resolve()

    count_result = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=workspace, capture_output=True, text=True,
    )
    if count_result.returncode != 0:
        error(f"Impossible de compter les commits: {count_result.stderr.strip()}")
        return 1
    count = int(count_result.stdout.strip())
    set_output("commits", count)
    if count < MIN_COMMITS:
        warning(
            f"Seulement {count} commits — minimum {MIN_COMMITS} requis "
            "pour être classé (trajectoire Kaizen)."
        )

    log_result = subprocess.run(
        ["git", "log", "--pretty=format:%H;%aI;%s"],
        cwd=workspace, capture_output=True, text=True,
    )
    if log_result.returncode != 0:
        error(f"Impossible d'exporter l'historique: {log_result.stderr.strip()}")
        return 1
    output = workspace / "artefact" / "commit-history.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(log_result.stdout, encoding="utf-8")
    print(f"Historique exporté: {output} ({count} commits)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
