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
  python scoring.py --org votre-org --repo tpsc-challenge
Variables d'environnement :
  GITHUB_TOKEN   : PAT avec accès public_repo (lecture issues + repos)
  SONAR_TOKEN    : token SonarCloud lecture
  IDENTITY_SALT  : sel secret de l'empreinte d'identité
  WINDOW_START   : ISO datetime d'ouverture de la nuit (optionnel)
"""

import argparse
import glob
import hashlib
import json
import math
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import requests
import yaml

GITHUB_API = "https://api.github.com"
SONAR_API = "https://sonarcloud.io/api"

# Notes Sonar -> points
MAINTENABILITY_POINTS = {"A": 15, "B": 10, "C": 5, "D": 0, "E": 0}
SECURITY_POINTS = {"A": 10, "B": 6, "C": 3, "D": 0, "E": 0}
COVERAGE_TARGET = 60.0          # % pour les 10 pts (proportionnel en dessous)
MIN_COMMITS = 20                # seuil d'éligibilité trajectoire


def gh_get(url: str, token: str, **params) -> requests.Response:
    r = requests.get(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }, params=params, timeout=30)
    if r.status_code == 403:  # rate limit : backoff simple
        time.sleep(int(r.headers.get("Retry-After", 60)))
        return gh_get(url, token, **params)
    return r


def sonar_get(path: str, token: str, **params) -> requests.Response:
    return requests.get(f"{SONAR_API}{path}", auth=(token, ""),
                        params=params, timeout=30)


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

    teams = []
    for path in glob.glob(f"{teams_dir}/*.yml"):
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data or "team-name" not in data:
            print(f"[warn] {path} invalide, ignoré", file=sys.stderr)
            continue
        teams.append(Team(data["team-name"], data["repo"],
                          data.get("sonar-org", ""), issue_number=0))
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
    return r.json().get("projectStatus", {}).get("status") == "OK"


def fetch_quality_measures(team: Team, token: str) -> dict:
    r = sonar_get("/measures/component", token,
                  component=team.project_key, organization=team.sonar_org,
                  branch="main",
                  metricKeys="reliability_rating,security_rating,sqale_rating,"
                             "coverage,duplicated_lines_density")
    if r.status_code != 200:
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
    s = Score()

    # --- Identité & éligibilité -------------------------------------
    ident = check_identity(team, cfg.gh_token, cfg.salt)
    if not ident["ok"]:
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

    return s, {"measures": measures, "commits": len(commits),
               "recoveries": recoveries, "identity": ident,
               "scans": len(history)}


def fetch_dependency_vulns(team: Team, token: str) -> tuple[int, int]:
    """Lit le rapport Trivy du dernier run du workflow d'appel.

    v1 : si aucun artefact exploitable, retourne (-1,-1) -> pas de points.
    À brancher sur l'API artifacts/du run (actions/runs -> artifacts).
    """
    return (-1, -1)


# ----------------------------------------------------------------------
# Main : batch -> data/leaderboard.json
# NB : la pente nécessite un archivage run après run. Chaque exécution
# lit data/scores-history.json (commit par l'Action) et y ajoute le
# score partiel courant : ainsi la trajectoire se construit toutes les
# 15 min même si l'API Sonar ne donne qu'un instantané.
# ----------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--org", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--window-start", default=os.environ.get("WINDOW_START"))
    args = p.parse_args()

    cfg = argparse.Namespace(
        gh_token=os.environ["GITHUB_TOKEN"],
        sonar_token=os.environ["SONAR_TOKEN"],
        salt=os.environ["IDENTITY_SALT"],
        window_start=datetime.fromisoformat(
            args.window_start or datetime.now(timezone.utc).isoformat()
        ),
        history_archive={},
    )

    # Historique des scores partiels accumulés au fil des batches
    try:
        with open("data/scores-history.json", encoding="utf-8") as f:
            cfg.history_archive = {k: v for k, v in json.load(f).items()}
    except FileNotFoundError:
        pass

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
            leaderboard.append({"team": team.name, "error": str(e)})

    leaderboard.sort(key=lambda e: e.get("score", -999), reverse=True)
    for rank, e in enumerate(leaderboard, 1):
        e["rank"] = rank

    os.makedirs("data", exist_ok=True)
    with open("data/leaderboard.json", "w", encoding="utf-8") as f:
        json.dump(leaderboard, f, ensure_ascii=False, indent=2)
    with open("data/scores-history.json", "w", encoding="utf-8") as f:
        json.dump(cfg.history_archive, f, ensure_ascii=False, indent=2)
    print(f"OK — {len(leaderboard)} équipes -> data/leaderboard.json")


if __name__ == "__main__":
    main()