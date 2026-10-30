#!/usr/bin/env python3
"""
TPS Challenge — Calculateur de score (batch).

S'exécute via GitHub Actions (schedule 15 min) dans Haingue/nuitdelinfo2026.
Pour chaque équipe inscrite (issues du repo), interroge les APIs SonarCloud
et GitHub, applique le barème officiel et produit data/leaderboard.json.

Barème (cf. énoncé) :
  A. Qualité finale (60) : gate 20 + maintenabilité 15 + sécurité 10 + couverture 10 + supply chain 5
  B. Kaizen (40) : pente 20 + résilience 10 + heijunka 10
  C. Bonus/malus : +5 / +3 / -5 / -10

Usage :
  python scoring.py --org Haingue --repo nuitdelinfo2026
Variables d'environnement :
  GITHUB_TOKEN   : PAT avec accès public_repo (lecture issues + repos)
  SONAR_TOKEN    : token SonarCloud lecture
  IDENTITY_SALT  : sel secret de l'empreinte d'identité
  WINDOW_START   : ISO datetime d'ouverture de la nuit (optionnel)
"""

import argparse
import glob
import hashlib
import io
import json
import logging
import math
import os
import sys
import time
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import requests
import yaml

GITHUB_API = "https://api.github.com"
SONAR_API = "https://sonarcloud.io/api"
logger = logging.getLogger(__name__)

# Notes Sonar -> points
MAINTENABILITY_POINTS = {"A": 15, "B": 10, "C": 5, "D": 0, "E": 0}
SECURITY_POINTS = {"A": 10, "B": 6, "C": 3, "D": 0, "E": 0}
COVERAGE_TARGET = 60.0          # % pour les 10 pts (proportionnel en dessous)
MIN_COMMITS = 20                # seuil d'éligibilité trajectoire


def gh_get(url: str, token: str, **params) -> requests.Response:
    logger.info("GitHub GET %s params=%s", url, params)
    r = requests.get(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }, params=params, timeout=30)
    logger.info("GitHub HTTP %s pour %s", r.status_code, url)
    if r.status_code == 403:  # rate limit : backoff simple
        delay = int(r.headers.get("Retry-After", 60))
        logger.warning("GitHub 403 pour %s : nouvelle tentative dans %s s", url, delay)
        time.sleep(delay)
        return gh_get(url, token, **params)
    return r


def sonar_get(path: str, token: str, **params) -> requests.Response:
    logger.info("SonarCloud GET %s%s params=%s", SONAR_API, path, params)
    response = requests.get(f"{SONAR_API}{path}", auth=(token, ""),
                            params=params, timeout=30)
    logger.info("SonarCloud HTTP %s pour %s%s", response.status_code, SONAR_API, path)
    return response


# ----------------------------------------------------------------------
# Équipe inscrite : issue d'inscription sur le repo du défi
# ----------------------------------------------------------------------
@dataclass
class Team:
    name: str
    repo_full: str            # "owner/repo"
    sonar_org: str           # clé SonarCloud déclarée à l'inscription
    issue_number: int

    @property
    def project_key(self) -> str:
        owner, name = self.repo_full.split("/")
        return f"{owner}_{name}"
    # NB : sonar_org ne peut PAS être dérivée du owner GitHub (SonarCloud
    # base la clé sur le display name à l'import) : elle vient de teams/<slug>.yml.


def load_teams(teams_dir: str = "teams") -> list[Team]:
    """Lit les fichiers d'équipe générés par le workflow d'inscription.

    Une seule source de vérité, versionée dans Git : teams/<team>.yml
    (team-name, repo, identity-hash). L'issue d'inscription n'est qu'un
    point d'entrée, le batch n'en dépend plus.
    """
    import glob

    logger.info("Chargement des equipes depuis %s", os.path.abspath(teams_dir))
    teams = []
    for path in glob.glob(f"{teams_dir}/*.yml"):
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data or "team-name" not in data:
            print(f"[warn] {path} invalide, ignoré", file=sys.stderr)
            continue
        teams.append(Team(data["team-name"], data["repo"],
                          data.get("sonar-org", ""), issue_number=0))
        logger.info("Equipe chargee : %s | https://github.com/%s | Sonar org=%s | fichier=%s",
                    teams[-1].name, teams[-1].repo_full, teams[-1].sonar_org, path)
    logger.info("%s equipe(s) chargee(s)", len(teams))
    if not teams:
        logger.warning("Aucune equipe trouvee : verifier le dossier teams et le repertoire courant")
    return teams


# ----------------------------------------------------------------------
# Identité : SHA-256(repository_id + team-name + SEL)
# ----------------------------------------------------------------------
def expected_identity_hash(team: Team, repo_id: int, salt: str) -> str:
    raw = f"{repo_id}{team.name}{salt}".encode()
    return hashlib.sha256(raw).hexdigest()


def check_identity(team: Team, token: str, salt: str) -> dict:
    r = gh_get(f"{GITHUB_API}/repos/{team.repo_full}", token)
    if r.status_code != 200:
        return {"ok": False, "reason": f"repo illisible ({r.status_code})"}
    info = r.json()
    if info.get("visibility") != "public":
        return {"ok": False, "reason": "repo non public"}
    return {"ok": True,
            "expected_hash": expected_identity_hash(team, info["id"], salt),
            "repo_id": info["id"],
            "created_at": info.get("created_at")}


# ----------------------------------------------------------------------
# Données qualité : SonarCloud
# ----------------------------------------------------------------------
def fetch_gate_current(team: Team, token: str) -> bool:
    r = sonar_get("/quality_gates/project_status", token,
                  project=team.project_key, organization=team.sonar_org,
                  branch="main")
    status = r.json().get("projectStatus", {}).get("status")
    logger.info("[%s] Quality Gate : %s", team.repo_full, status or "indisponible")
    return status == "OK"


def fetch_quality_measures(team: Team, token: str) -> dict:
    r = sonar_get("/measures/component", token,
                  component=team.project_key, organization=team.sonar_org,
                  branch="main",
                  metricKeys="reliability_rating,security_rating,sqale_rating,"
                             "coverage,duplicated_lines_density")
    if r.status_code != 200:
        logger.warning("[%s] Mesures Sonar indisponibles : HTTP %s", team.repo_full, r.status_code)
        return {}
    return {m["metric"]: m.get("value")
            for m in r.json().get("component", {}).get("measures", [])}


def fetch_scan_history(team: Team, token: str,
                       window_start: datetime) -> list[datetime]:
    """Historique des analyses Sonar de la nuit (API ce/activity, publique)."""
    fmt = window_start.strftime("%Y-%m-%dT%H:%M%z")
    r = sonar_get("/ce/activity", token, component=team.project_key,
                  **{"from": fmt, "onlyCurrentBranch": "true"})
    if r.status_code != 200:
        return []
    return sorted(
        datetime.fromisoformat(t["submittedAt"].replace("Z", "+00:00"))
        for t in r.json().get("tasks", [])
        if t.get("status") == "SUCCESS"
    )


# ----------------------------------------------------------------------
# Données rythme : GitHub (commits + runs CI)
# ----------------------------------------------------------------------
def fetch_commits(team: Team, token: str, since: datetime) -> list[dict]:
    commits, page = [], 1
    while True:
        r = gh_get(f"{GITHUB_API}/repos/{team.repo_full}/commits", token,
                   since=since.isoformat(), per_page=100, page=page)
        if r.status_code != 200 or not r.json():
            break
        commits.extend(r.json())
        if len(r.json()) < 100:
            break
        page += 1
    return commits


def fetch_workflow_runs(team: Team, token: str) -> list[dict]:
    """Runs du workflow d'appel : base de la résilience Jidoka."""
    r = gh_get(f"{GITHUB_API}/repos/{team.repo_full}/actions/runs", token,
               per_page=100, status="completed")
    return [run for run in r.json().get("workflow_runs", [])
            if run["name"] == "TPS Challenge — Appel de l'usine qualité"]


# ----------------------------------------------------------------------
# Barème
# ----------------------------------------------------------------------
@dataclass
class Score:
    quality: float = 0.0
    pente: float = 0.0
    resilience: float = 0.0
    heijunka: float = 0.0
    bonus: float = 0.0
    total: float = 0.0
    eligible: bool = False


def heijunka_score(commit_times: list[datetime]) -> float:
    """10 pts : entropie de Shannon de la distribution horaire des commits.

    ~10 = commits répartis (max entropie) ; ~0 = rush final.
    """
    if not commit_times:
        return 0.0
    buckets: dict[int, int] = {}
    for t in commit_times:
        buckets[t.hour] = buckets.get(t.hour, 0) + 1
    total = sum(buckets.values())
    entropy = -sum((n / total) * math.log2(n / total)
                   for n in buckets.values())
    max_entropy = math.log2(len(buckets)) or 1.0
    return round(10 * entropy / max_entropy, 2)


def score_team(team: Team, cfg) -> tuple[Score, dict]:
    logger.info("Debut scoring : %s | https://github.com/%s | projet Sonar=%s | org=%s",
                team.name, team.repo_full, team.project_key, team.sonar_org)
    s = Score()

    # --- Identité & éligibilité -------------------------------------
    ident = check_identity(team, cfg.gh_token, cfg.salt)
    if not ident["ok"]:
        logger.warning("[%s] Evaluation interrompue : %s", team.repo_full, ident["reason"])
        return s, {"error": ident["reason"]}

    # --- A. Qualité finale (60) --------------------------------------
    measures = fetch_quality_measures(team, cfg.sonar_token)
    gate_current = fetch_gate_current(team, cfg.sonar_token)
    if gate_current:
        s.quality += 20
    s.quality += MAINTENABILITY_POINTS.get(measures.get("sqale_rating"), 0)
    s.quality += SECURITY_POINTS.get(measures.get("security_rating"), 0)
    coverage = float(measures.get("coverage") or 0)
    s.quality += round(min(coverage / COVERAGE_TARGET, 1.0) * 10, 2)
    # Supply chain (5) : lu depuis l'artefact Trivy du dernier run
    crit, high = fetch_dependency_vulns(team, cfg.gh_token)
    if crit == 0 and high == 0:
        s.quality += 5
    logger.info("[%s] Qualite=%s/60 | mesures=%s | Trivy CRITICAL=%s HIGH=%s",
                team.repo_full, s.quality, measures, crit, high)

    # --- B. Kaizen (40) ----------------------------------------------
    history = fetch_scan_history(team, cfg.sonar_token, cfg.window_start)

    # Pente (20) : trajectoire de la composante qualité depuis le début de
    # la nuit. scores-history.json archive un snapshot complet par batch
    # (ts + tous les sous-scores) -> sert aussi au graphique de progression.
    archive = cfg.history_archive.get(team.name, [])
    if archive:
        first = archive[0]["qualite"]
        s.pente = round(max((s.quality - first) / 30 * 20, 0), 2)
        s.pente = min(s.pente, 20)

    # Résilience (10) : runs rouges repassés au vert (2.5 pts par redressement)
    runs = sorted(fetch_workflow_runs(team, cfg.gh_token),
                  key=lambda r: r["created_at"])
    red, recoveries = 0, 0
    for run in runs:
        if run["conclusion"] == "failure":
            red += 1
        else:
            if red:
                recoveries += 1
            red = 0
    s.resilience = min(recoveries * 2.5, 10)

    # Heijunka (10)
    commits = fetch_commits(team, cfg.gh_token, cfg.window_start)
    logger.info("[%s] Depuis %s : %s commits | %s analyses Sonar | %s runs CI examines | %s redressements | %s snapshots archives",
                team.repo_full, cfg.window_start.isoformat(), len(commits),
                len(history), len(runs), recoveries, len(archive))
    times = [datetime.fromisoformat(c["commit"]["author"]["date"].replace("Z", "+00:00"))
             for c in commits]
    s.heijunka = heijunka_score(times)

    # --- C. Bonus / malus --------------------------------------------
    if red == 0 and not any(r["conclusion"] == "failure" for r in runs):
        s.bonus += 5    # jamais resté rouge sur la fenêtre analysée
    if len(archive) >= 2 and archive[-1]["total"] < archive[-2]["total"]:
        s.bonus -= 5    # dernier batch en régression
    if not gate_current:
        s.bonus -= 10   # gate rouge à la livraison

    s.total = round(s.quality + s.pente + s.resilience + s.heijunka + s.bonus, 2)
    s.eligible = len(commits) >= MIN_COMMITS and gate_current
    logger.info("[%s] Score total=%s | qualite=%s pente=%s resilience=%s heijunka=%s bonus=%s | eligible=%s (commits=%s/%s, gate=%s)",
                team.repo_full, s.total, s.quality, s.pente, s.resilience,
                s.heijunka, s.bonus, s.eligible, len(commits), MIN_COMMITS, gate_current)

    return s, {"measures": measures, "commits": len(commits),
               "recoveries": recoveries, "identity": ident,
               "supply_chain": {"critical": crit, "high": high},
               "scans": len(history)}


def fetch_dependency_vulns(team: Team, token: str) -> tuple[int, int]:
    """Lit Trivy sur le dernier run termine de main, meme si Sonar echoue.

    Un rapport absent, invalide ou aux versions non resolues vaut (-1, -1).
    """
    try:
        runs = [run for run in fetch_workflow_runs(team, token)
                if run.get("head_branch") == "main"]
        if not runs:
            logger.warning("[%s] Trivy indisponible : aucun run termine sur main", team.repo_full)
            return (-1, -1)
        latest = max(runs, key=lambda run: run["created_at"])
        logger.info("[%s] Run Trivy selectionne : https://github.com/%s/actions/runs/%s (date=%s)",
                    team.repo_full, team.repo_full, latest["id"], latest["created_at"])
        response = gh_get(
            f"{GITHUB_API}/repos/{team.repo_full}/actions/runs/{latest['id']}/artifacts",
            token, per_page=100,
        )
        response.raise_for_status()
        artifact = next((entry for entry in response.json().get("artifacts", [])
                         if entry.get("name") == "trivy-report"
                         and not entry.get("expired", False)), None)
        if artifact is None:
            logger.warning("[%s] Trivy indisponible : artefact absent ou expire sur le run %s",
                           team.repo_full, latest["id"])
            return (-1, -1)
        logger.info("[%s] Telechargement artefact trivy-report id=%s", team.repo_full, artifact["id"])
        response = gh_get(
            f"{GITHUB_API}/repos/{team.repo_full}/actions/artifacts/{artifact['id']}/zip",
            token,
        )
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            report = json.loads(archive.read("trivy-report.json"))
        results = report["Results"]
        if not isinstance(results, list):
            logger.warning("[%s] Trivy invalide : Results n'est pas une liste", team.repo_full)
            return (-1, -1)
        critical, high = 0, 0
        for result in results:
            if result.get("Class") == "lang-pkgs" and any(
                not package.get("Version")
                for package in result.get("Packages", [])
            ):
                logger.warning("[%s] Trivy incomplet : versions non resolues pour %s, aucun point supply chain",
                               team.repo_full, result.get("Target", "cible inconnue"))
                return (-1, -1)
            for vulnerability in result.get("Vulnerabilities", []):
                critical += vulnerability.get("Severity") == "CRITICAL"
                high += vulnerability.get("Severity") == "HIGH"
            logger.info("[%s] Trivy : CRITICAL=%s HIGH=%s", team.repo_full, critical, high)
        return critical, high
    except (requests.RequestException, zipfile.BadZipFile, KeyError,
            ValueError, TypeError, AttributeError) as error:
        logger.warning("[%s] Trivy indisponible : %s", team.repo_full, type(error).__name__)
        return (-1, -1)


# ----------------------------------------------------------------------
# Main : batch -> data/leaderboard.json
# NB : la pente nécessite un archivage run après run. Chaque exécution
# lit data/scores-history.json (commit par l'Action) et y ajoute le
# score partiel courant : ainsi la trajectoire se construit toutes les
# 15 min même si l'API Sonar ne donne qu'un instantané.
# ----------------------------------------------------------------------
def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--org", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--window-start", default=os.environ.get("WINDOW_START"))
    args = p.parse_args()
    logger.info("Batch demarre | depot du defi=https://github.com/%s/%s | cwd=%s",
                args.org, args.repo, os.getcwd())
    if not args.window_start:
        logger.warning("WINDOW_START absent : la fenetre commence maintenant, les commits anterieurs ne seront pas comptes")

    cfg = argparse.Namespace(
        gh_token=os.environ["GITHUB_TOKEN"],
        sonar_token=os.environ["SONAR_TOKEN"],
        salt=os.environ["IDENTITY_SALT"],
        window_start=datetime.fromisoformat(
            args.window_start or datetime.now(timezone.utc).isoformat()
        ),
        history_archive={},
    )
    logger.info("Debut de la fenetre de scoring : %s", cfg.window_start.isoformat())

    # Historique des scores partiels accumulés au fil des batches
    try:
        with open("data/scores-history.json", encoding="utf-8") as f:
            cfg.history_archive = {k: v for k, v in json.load(f).items()}
        logger.info("Historique charge : %s equipes", len(cfg.history_archive))
    except FileNotFoundError:
        logger.info("Aucun historique precedent : premier snapshot de progression")

    teams = load_teams("teams")
    leaderboard = []
    for team in teams:
        try:
            score, details = score_team(team, cfg)
            # archive la trajectoire pour la pente + le suivi détaillé par équipe
            if "error" not in details:
                snapshot = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "total": score.total,
                    "qualite": score.quality,
                    "pente": score.pente,
                    "resilience": score.resilience,
                    "heijunka": score.heijunka,
                    "bonus_malus": score.bonus,
                }
                cfg.history_archive.setdefault(team.name, []).append(snapshot)
            leaderboard.append({
                "team": team.name,
                "repo": team.repo_full,
                "score": score.total,
                "breakdown": {
                    "qualite": score.quality,
                    "pente": score.pente,
                    "resilience": score.resilience,
                    "heijunka": score.heijunka,
                    "bonus_malus": score.bonus,
                },
                "eligible": score.eligible,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": details,
            })
        except Exception as e:  # une équipe ne casse jamais le batch
            logger.error("Echec scoring pour %s | https://github.com/%s | erreur=%s",
                         team.name, team.repo_full, type(e).__name__)
            leaderboard.append({"team": team.name, "error": str(e)})

    leaderboard.sort(key=lambda e: e.get("score", -999), reverse=True)
    for rank, e in enumerate(leaderboard, 1):
        e["rank"] = rank

    os.makedirs("data", exist_ok=True)
    with open("data/leaderboard.json", "w", encoding="utf-8") as f:
        json.dump(leaderboard, f, ensure_ascii=False, indent=2)
    with open("data/scores-history.json", "w", encoding="utf-8") as f:
        json.dump(cfg.history_archive, f, ensure_ascii=False, indent=2)
    logger.info("Batch termine : %s equipes | classement=%s | historique=%s",
                len(leaderboard), os.path.abspath("data/leaderboard.json"),
                os.path.abspath("data/scores-history.json"))
    print(f"OK — {len(leaderboard)} équipes -> data/leaderboard.json")


if __name__ == "__main__":
    main()