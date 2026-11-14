#!/usr/bin/env python3
"""
Jidoka — Contrôle de conformité pour Quality Factory.

Reproduit le job `conformite` du workflow quality.yml :
1. Récupère le fichier d'équipe généré à l'inscription (teams/<slug>.yml).
2. Vérifie l'empreinte d'identité et l'organisation SonarCloud déclarées.
3. Compare le bloc d'appel du repo de l'équipe au bloc généré par Toyota
   (normalisation CRLF/espaces puis comparaison SHA-256).
4. Vérifie que le repository est public (API REST GitHub, token GH_TOKEN).
"""

import argparse
import difflib
import hashlib
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).parent.parent))

from quality_factory.utils.github import error, notice


def fetch(url: str, token: str = "") -> str:
    """Télécharge une URL et retourne le contenu texte (lève en cas d'échec)."""
    request = Request(url)
    if token:
        request.add_header("Authorization", f"Bearer {token}")
        request.add_header("Accept", "application/vnd.github+json")
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def slugify(team_name: str) -> str:
    """Slug identique à celui du workflow d'inscription."""
    return re.sub(r"[^a-z0-9-]", "-", team_name.lower()).strip("-")


def extract_field(team_file: str, field: str) -> str:
    """Extrait un champ `field: "valeur"` du fichier d'équipe."""
    match = re.search(rf'^{re.escape(field)}: *"(.*)"$', team_file, re.MULTILINE)
    return match.group(1) if match else ""


def extract_call_block(team_file: str) -> str:
    """Extrait le bloc d'appel entre les marqueurs (exclusifs) du fichier d'équipe."""
    lines = []
    capturing = False
    for line in team_file.splitlines():
        if capturing and line.startswith("# === FIN DU FICHIER"):
            break
        if capturing:
            lines.append(line)
        if re.match(r"^# === FICHIER D.APPEL", line):
            capturing = True
    return "\n".join(lines)


def normalize(content: str) -> str:
    """
    Normalisation anti CRLF/LF : suppression des \\r et des espaces/tabs de fin
    de ligne, des lignes vides finales, avec un unique retour à la ligne final.
    """
    lines = [re.sub(r"[ \t]+$", "", line.rstrip("\r")) for line in content.splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Quality Factory - Jidoka, contrôle de conformité"
    )
    parser.add_argument("--team-name", required=True, help="Nom de l'équipe inscrit")
    parser.add_argument("--identity-hash", required=True, help="Empreinte d'identité fournie à l'inscription")
    parser.add_argument("--sonar-org", required=True, help="Organisation SonarCloud déclarée")
    parser.add_argument("--challenge-repo", required=True, help="Dépôt du challenge (owner/repo)")
    parser.add_argument("--repository", required=True, help="Dépôt GitHub de l'équipe (owner/repo)")
    parser.add_argument("--ref-name", required=True, help="Branche de l'exécution (github.ref_name)")
    parser.add_argument("--workflow-ref", required=True, help="Référence du workflow appelant (github.workflow_ref)")
    args = parser.parse_args()

    # 1. Fichier d'équipe généré à l'inscription
    slug = slugify(args.team_name)
    team_url = f"https://raw.githubusercontent.com/{args.challenge_repo}/main/teams/{slug}.yml"
    try:
        team_file = fetch(team_url)
    except (HTTPError, URLError, TimeoutError):
        team_file = ""
    if not team_file.strip():
        error(
            f"Aucun fichier d'inscription trouvé pour l'équipe '{args.team_name}' "
            f"(teams/{slug}.yml). Vérifiez votre inscription sur {args.challenge_repo}."
        )
        return 1

    # 2. Empreinte d'identité + organisation SonarCloud
    expected_hash = extract_field(team_file, "identity-hash")
    if not expected_hash:
        error("Fichier d'équipe invalide (empreinte absente).")
        return 1
    if args.identity_hash != expected_hash:
        error("Empreinte d'identité invalide pour cette équipe.")
        return 1
    # La clé d'org SonarCloud ne peut PAS être dérivée du login GitHub
    # (SonarCloud la base sur le display name à l'import) : elle est
    # déclarée à l'inscription et verrouillée ici comme l'empreinte.
    expected_org = extract_field(team_file, "sonar-org")
    if not expected_org:
        error("Fichier d'équipe invalide (organisation SonarCloud absente).")
        return 1
    if args.sonar_org != expected_org:
        error("Clé d'organisation SonarCloud invalide pour cette équipe.")
        return 1
    notice("Empreinte d'identité + organisation SonarCloud conformes ✔")
    # NB : la validité cryptographique de l'empreinte (SHA-256 de
    # repository_id + team-name + SEL secret) est re-vérifiée côté batch
    # Toyota, où le sel est conservé.

    # 3. Bloc d'appel identique au bloc généré par Toyota
    # workflow_ref = "owner/repo/.github/workflows/<fichier>@refs/heads/main"
    caller_file = os.path.basename(args.workflow_ref.split("@", 1)[0])
    caller_url = (
        f"https://raw.githubusercontent.com/{args.repository}/{args.ref_name}"
        f"/.github/workflows/{caller_file}"
    )
    try:
        caller = fetch(caller_url)
    except (HTTPError, URLError, TimeoutError):
        error(f"Impossible de récupérer le fichier d'appel ({caller_file}) du repo de l'équipe.")
        return 1

    expected_block = extract_call_block(team_file)
    if not expected_block.strip():
        error("Bloc d'appel introuvable dans le fichier d'équipe — contactez les organisateurs.")
        print("--- Diagnostic : 30 premières lignes du fichier d'équipe ---")
        print("\n".join(team_file.splitlines()[:30]))
        print("-----------------------------------------------------------")
        return 1

    expected_norm = normalize(expected_block)
    caller_norm = normalize(caller)
    if sha256(caller_norm) != sha256(expected_norm):
        error("Fichier d'appel non conforme au fichier généré lors de votre inscription. Restaurez-le sans le modifier.")
        print("--- Diagnostic : premières divergences (attendu vs copié) ---")
        diff = difflib.unified_diff(
            expected_norm.splitlines(), caller_norm.splitlines(),
            fromfile="attendu", tofile="copié", lineterm="",
        )
        for line in list(diff)[:20]:
            print(line)
        print("-----------------------------------------------------------")
        return 1
    notice("Fichier d'appel conforme ✔")

    # 4. Repository public (requis pour l'évaluation)
    token = os.environ.get("GH_TOKEN", "")
    try:
        import json
        repo_info = json.loads(fetch(f"https://api.github.com/repos/{args.repository}", token))
        visibility = repo_info.get("visibility", "unknown")
    except (HTTPError, URLError, TimeoutError, ValueError):
        visibility = "unknown"
    if visibility != "public":
        error("Le repository doit être public (requis pour l'évaluation).")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
