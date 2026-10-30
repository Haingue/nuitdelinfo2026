# 🏭 TPS Challenge — Documentation d'architecture

> Le défi Toyota de la Nuit de l'Info : les équipes construisent une **usine logicielle**, nous mesurons leur qualité et leur trajectoire, automatiquement, à grande échelle.

## 1. Vue d'ensemble

Trois acteurs, deux repos, zéro serveur :

```text
┌─────────────┐   issue d'inscription    ┌──────────────────────────┐
│   Équipe    │ ───────────────────────► │  Haingue/nuitdelinfo2026 │
│ (repo public│                          │       (repo du défi)     │
│  + SONAR_   │ ◄─────────────────────── │                           │
│  TOKEN)     │  fichier d'appel + hash  │  inscription.yml  (bot)   │
└──────┬──────┘                          │  quality.yml      (CI)    │
       │ push sur main                   │  leaderboard.yml  (batch) │
       ▼                                 │  scoring/scoring.py       │
┌─────────────┐   scan + audit à chaque  │  teams/<slug>.yml         │
│  SonarCloud │   push                   │  data/*.json             │
│  + Trivy CI │ ◄──────────────────────── │  leaderboard/ (SPA)      │
└─────────────┘                          └────────────┬─────────────┘
                                                      │ GitHub Pages
                                                      ▼
                                              Leaderboard public
```

- **Repos des équipes** : code + fichier d'appel + secret `SONAR_TOKEN`. Rien d'autre à configurer.
- **Repo du défi** : toute la mécanique. Les équipes ne peuvent modifier aucune règle : elles appellent un workflow *réutilisable* pointé sur ce repo (tag `v1`), dont la logique vit ici.

## 2. Les composants


| Composant                | Fichier                                  | Rôle                                                                                                                                                   |
| ------------------------ | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Formulaire d'inscription | `.github/ISSUE_TEMPLATE/inscription.yml` | Point d'entrée unique des équipes (issue labellisée `inscription`)                                                                                     |
| Bot d'inscription        | `.github/workflows/inscription.yml`      | Valide (repo public, unicité), calcule l'empreinte, génère `teams/<slug>.yml`, commite, répond dans l'issue                                            |
| Usine qualité            | `.github/workflows/quality.yml`          | Workflow réutilisable : conformité (hash + empreinte), scan Sonar, Trivy, Heijunka, rapport                                                            |
| Calculateur              | `scoring/scoring.py`                     | Batch Python : lit `teams/*.yml`, interroge APIs SonarCloud + GitHub, applique le barème, produit `data/leaderboard.json` + `data/scores-history.json` |
| Batch + déploiement      | `.github/workflows/leaderboard.yml`      | Cron 15 min : exécute le calculateur, commit les données, build la SPA, déploie GitHub Pages                                                           |
| Leaderboard              | `leaderboard/`                           | SPA React + Vite + Tailwind : podium, liste, sparklines, détail par équipe (progression multi-courbes)                                                 |


## 3. Le process complet (cycle de vie d'une équipe)

1. **Inscription** — l'équipe ouvre une issue (formulaire) avec nom d'équipe + URL du repo.
2. **Bot** — vérifie le repo (public, existant, non déjà inscrit), récupère son `repository_id`, calcule l'empreinte `SHA-256(repository_id + team-name + IDENTITY_SALT)`, génère `teams/<slug>.yml` (métadonnées + bloc d'appel délimité), committe, et répond dans l'issue avec le bloc d'appel à copier **tel quel**.
3. **Setup équipe** — copie le bloc dans `.github/workflows/appeler-tps-challenge.yml`, crée son compte SonarCloud, ajoute le secret `SONAR_TOKEN`.
4. **À chaque push sur `main`** — `quality.yml` s'exécute dans le contexte du repo équipe :
  - *conformité* : slug → `teams/<slug>.yml`, empreinte d'entrée == empreinte enregistrée, fichier d'appel == bloc extrait (hash SHA-256, byte pour byte) ;
  - *Sonar* : scan complet (exclusions imposées par nous), Quality Gate **bloquant** ;
  - *Trivy* : vulnérabilités HIGH/CRITICAL des dépendances (artefact `trivy-report`) ;
  - *Heijunka* : export de l'historique de commits (artefact `heijunka-history`) ;
  - *rapport* : métriques de cette exécution et dernier score officiel publié dans `data/leaderboard.json`, sélectionné par dépôt, avec rang, éligibilité, détail et horodatage. Le score peut ne pas encore inclure l'exécution courante ; s'il est absent ou inaccessible, le résumé le signale sans faire échouer le workflow.
5. **Toutes les 15 min** — `leaderboard.yml` : le batch évalue toutes les équipes de `teams/`, archivage d'un snapshot complet par équipe (`scores-history.json`), commit des données, build + déploiement Pages.
6. **En continu** — la SPA affiche le classement live ; au clic sur une équipe : progression détaillée de chaque composante du score.

## 4. Barème (rappel)

**Qualité finale 60** (gate 20, maintenabilité 15, sécurité 10, couverture 10, supply chain 5) · **Kaizen 40** (pente 20, résilience 10, heijunka 10) · **Bonus/malus** (jamais rouge +5, régression corrigée +3, régression finale −5, gate rouge final −10). Éligibilité : ≥ 20 commits, gate vert final, repo public. La **pente** se calcule sur la trajectoire archivée par le batch (première vs dernière mesure qualité), pas sur un instantané Sonar.

## 5. Sécurité &amp; anti-triche — le modèle de menaces


| Menace                       | Parade                                                                                                                             | Où                               |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| Modifier le workflow qualité | Workflow réutilisable : la logique vit dans notre repo, tag `v1` contrôlé par nous                                                 | architecture                     |
| Modifier le fichier d'appel  | Hash SHA-256 du bloc vs `teams/<slug>.yml`, à chaque push                                                                          | quality.yml/conformité           |
| Usurper une autre équipe     | Empreinte = SHA-256(repo\_id + team + **sel secret**) ; vérifiée en CI (valeur enregistrée) **et** en batch (recalcul avec le sel) | inscription + conformité + batch |
| Exclure des fichiers du scan | `-Dsonar.exclusions` imposé dans notre workflow ; paramètres Sonar re-vérifiés via API                                             | quality.yml/sonar + batch        |
| Envoyer de faux scores       | **Pull, jamais push** : les équipes n'envoient rien ; le batch lit les APIs directement                                            | leaderboard.yml                  |
| Multi-inscriptions / flood   | Unicité nom + repo dans le bot ; un fichier `teams/` par équipe ; `concurrency` sur le batch                                       | inscription.yml                  |
| Contestation                 | Tout est commité et horodaté : inscriptions, fichiers d'équipe, chaque leaderboard, snapshots de scores                            | Git = audit trail                |


**Secrets** (repo du défi) : `GH_PAT` (lecture API, attention aux rate limits), `SONAR_TOKEN` (SonarCloud, lecture), `IDENTITY_SALT` (sel de l'empreinte — ne vit **jamais** en CI côté équipes). **Variable** : `WINDOW_START` (ouverture de la nuit). **Labels** à créer : `inscription`, `inscrit ✅`.

## 6. Subtilités d'implémentation (les pièges rencontrés)

1. **Hash sur contenu normalisé.** Les deux fichiers sont normalisés avant hachage : `\r` supprimés (CRLF→LF), espaces/tabs de fin de ligne supprimés, lignes vides finales retirées, un unique saut de ligne final. Les équipes Windows ne peuvent donc pas échouer sur les fins de ligne — seul le contenu significatif compte. Restent piégeux : apostrophe typographique `'`, caractères Unicode convertis par l'éditeur, lignes avalées par un copier-coller Markdown.
2. **Une seule définition du bloc d'appel.** Le bot et le workflow qualité extraient le bloc avec le *même* `awk` borné — sinon le message copié et la référence vérifiée divergent.
3. **Slug cohérent** : `team-name` → slug (minuscules, non-alnum → tirets) calculé à l'identique dans le bot et dans la conformité CI. `TMMF_TEST` → `tmmf-test`.
4. **Contexte `workflow_call`** : `github.event.repository` n'est pas fiable ; utiliser `github.repository`. `github.workflow_ref` donne le chemin du fichier appelant.
5. **Empreinte en CI vs batch** : la CI compare la valeur *enregistrée* (pas de sel exposé) ; la validité cryptographique (sel) est re-vérifiée seulement côté batch. Le sel ne doit jamais apparaître dans un workflow exposé aux équipes.
6. **Pente Kaizen** : l'API Sonar ne donne qu'un instantané → la trajectoire vient de l'archivage batch (`scores-history.json`, un snapshot complet par run 15 min). Les premières minutes de la nuit, la pente est donc nulle par construction.
7. **Bash dans les workflows** : heredocs non quotés interprètent les backticks Markdown → messages cassés. Construire les messages avec `echo` + `--body-file`.
8. **`sed` BRE** : parenthèses littérales vs `\(\)` — piège classique sur l'extraction de l'empreinte.
9. **Quality Gate bloquant** : `scanMetadataReportFile: .scannerwork/report-task.txt` (scanner manuel) + `SONAR_TOKEN` en env du step de gate.
10. **Anti-boucle** : `leaderboard.yml` n'écoute que `schedule`/`workflow_dispatch` ; les commits du bot portent `[skip ci]`.
11. **Rate limits à 6000 équipes** : PAT GitHub = 5000 req/h ; backoff sur 403 dans `scoring.py`. À re-tester en charge. Vérifier aussi le quota d'analyses SonarCloud gratuit.
  Les métriques entre jobs transitent par `$GITHUB_OUTPUT`, les sorties du job et `needs.<job>.outputs` : `$GITHUB_ENV` reste local à un job. Le rapport affiche le nombre total de commits du dépôt ; le batch applique le seuil d'éligibilité aux commits de la fenêtre du défi.
12. **`fetch_dependency_vulns` (scoring.py)** : en stub v1 — à brancher sur l'artefact `trivy-report` du dernier run (5 pts supply chain).
13. **Un repo, un owner, un import SonarCloud, une clé déclarée** : la clé d'org SonarCloud d'une équipe **ne peut pas être dérivée du login GitHub** — SonarCloud la base sur le display name à l'import (constaté en test : login `Haingue` → org `FabienH`). Elle est donc déclarée dans l'issue d'inscription, stockée dans `teams/<slug>.yml` (métadonnée `sonar-org`), passée en entrée du workflow d'appel et **verrouillée en CI** comme l'empreinte. Le batch la lit du fichier d'équipe. L'import SonarCloud doit être fait par le **propriétaire du repo** (ou un admin si l'équipe est sous une org GitHub) ; les autres membres sont de simples collaborateurs.

## 7. Mise en route (nouvel événement)

1. Créer les labels `inscription` et `inscrit ✅`, les secrets `GH_PAT`/`SONAR_TOKEN`/`IDENTITY_SALT`, la variable `WINDOW_START`.
2. Configurer l'organisation **SonarCloud** du challenge et renseigner `SONAR_ORG` dans `quality.yml`.
3. Pousser tous les workflows ; taguer le workflow qualité : `git tag -f v1 && git push -f origin v1`.
4. Activer GitHub Pages (source : GitHub Actions).
5. Test bout en bout avec un repo pilote (inscription réelle, push, batch manuel, vérification du leaderboard).
6. Le jour J : régler `WINDOW_START` à l'ouverture ; surveiller les 403/429 dans les logs batch.