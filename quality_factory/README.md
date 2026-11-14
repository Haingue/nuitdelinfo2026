# Quality Factory

Usine de tests pour le challenge **Nuit de l'Info 2026** - Toyota Production System

Ce module contient toute la logique du workflow `quality.yml` : un script par job, exécuté dans l'image Docker (qui embarque Java 21, Maven, Gradle, Node + pnpm, Python, **sonar-scanner** et **Trivy**).

| Job du workflow | Script |
|---|---|
| `conformite` | `conformite.py` — fichier d'équipe, empreinte, bloc d'appel, repo public |
| `sonar` | `sonar.py` — scan SonarCloud, Quality Gate, export du rapport |
| `tests` | `tests.py` — détection + exécution des suites avec couverture, sortie `status` |
| `dependances` | `dependances.py` — pré-résolution Maven, Trivy, métriques |
| `rythme` | `rythme.py` — comptage des commits, export de l'historique |
| `rapport` | `rapport.py` — synthèse et score officiel dans le résumé de la run |

## 📁 Structure

```
quality_factory/
├── conformite.py           # Job conformite (Jidoka)
├── sonar.py                # Job sonar (scan + Quality Gate + rapport)
├── tests.py                # Job tests (détection + exécution des suites)
├── dependances.py          # Job dependances (Maven go-offline + Trivy)
├── rythme.py               # Job rythme (Heijunka)
├── rapport.py              # Job rapport (résumé de la run)
├── config.py              # Configuration centrale
├── models.py              # Modèles de données
├── detect/
│   ├── __init__.py
│   ├── python.py           # Détection des projets Python
│   ├── java.py             # Détection des projets Java
│   └── node.py             # Détection des projets Node
├── runners/
│   ├── __init__.py
│   ├── python_runner.py    # Exécution des tests Python
│   ├── java_runner.py      # Exécution des tests Java
│   └── node_runner.py      # Exécution des tests Node
├── report.py              # Génération du rapport
├── utils/
│   ├── __init__.py
│   ├── command.py          # Utilitaires pour les commandes
│   ├── github.py           # Utilitaires GitHub Actions (outputs, summary)
│   └── path.py             # Utilitaires pour les chemins
├── requirements.txt        # Dépendances Python
├── run.sh                 # Script d'exécution
├── Dockerfile             # Image Docker
└── README.md
```

## 🚀 Utilisation

### 1. Exécution locale (sans conteneur)

#### Prérequis
- Python 3.11+
- Java 21+ (pour les projets Java)
- Node.js 20+ (pour les projets Node)
- Maven et Gradle (pour les projets Java)

#### Installation

```bash
# Créer un environnement virtuel
python3 -m venv quality_factory/.venv

# Activer l'environnement
source quality_factory/.venv/bin/activate  # Linux/Mac
# ou sur Windows: quality_factory\.venv\Scripts\activate

# Installer les dépendances
pip install -r quality_factory/requirements.txt
```

#### Exécution

```bash
# Mode normal (détection + exécution)
python3 quality_factory/tests.py --workspace /chemin/du/projet

# Mode dry-run (détection uniquement)
python3 quality_factory/tests.py --workspace /chemin/du/projet --dry-run

# Avec toutes les options
python3 quality_factory/tests.py \
    --workspace /chemin/du/projet \
    --coverage-dir /chemin/des/rapports \
    --results-file /chemin/du/rapport.json \
    --temp-dir /tmp \
    --verbose
```

#### Utilisation du script d'exécution

```bash
# Donner les permissions
chmod +x quality_factory/run.sh

# Exécuter
./quality_factory/run.sh

# Avec des options supplémentaires
./quality_factory/run.sh --dry-run
```

### 2. Exécution avec Docker

L'image est basée sur **`buildpack-deps:noble`** (image officielle Docker,
Ubuntu 24.04 — même base que les runners `ubuntu-latest` de GitHub Actions) :
elle fournit d'origine git, curl, build-essential et les bibliothèques de
développement usuelles. Sont ajoutés : **Java 21** (+ Maven, Gradle 8.8),
**Python 3.12** et **Node.js 22** (tarball officiel épinglé + pnpm).

#### Build de l'image

```bash
# Contexte de build = racine du dépôt
docker build -t quality_factory -f quality_factory/Dockerfile .
```

> **Proxy d'entreprise (inspection TLS)** : déposez les certificats CA du
> proxy (`.crt`, PEM) dans [`certs/`](./certs/README.md) avant le build. Ils
> sont intégrés au magasin système, au truststore Java et pris en compte par
> npm/pnpm et pip. Sans certificat, le build fonctionne normalement.

#### Exécution

```bash
# Monter le workspace et exécuter
docker run -v $(pwd):/workspace -v $(pwd)/coverage-artifacts:/coverage-artifacts \
    quality_factory \
    --workspace /workspace \
    --coverage-dir /coverage-artifacts \
    --results-file /workspace/test-results.json
```

> **Windows (Docker Desktop)** : les bind mounts de chemins Windows ne
> supportent pas les `rename` de répertoires utilisés par pnpm
> (`ERR_PNPM_EACCES`). Pour tester en local, copiez le workspace dans le
> filesystem du conteneur (comme le fera la CI) :
>
> ```powershell
> docker run --rm -v "C:\chemin\projet:/mnt/src:ro" --entrypoint bash quality_factory `
>     -c "cp -r /mnt/src /work && /opt/venv/bin/python3 -u /quality_factory/tests.py --workspace /work --verbose"
> ```

## 🔧 Options CLI

| Option | Description | Défaut |
|--------|-------------|--------|
| `--workspace` | Répertoire de travail | Répertoire courant |
| `--coverage-dir` | Dossier de sortie des rapports de couverture | `<workspace>/coverage-artifacts` |
| `--results-file` | Fichier de sortie du rapport JSON | `<workspace>/test-results.json` |
| `--temp-dir` | Dossier temporaire | `/tmp` |
| `--dry-run` | Mode test: détection uniquement | - |
| `--verbose` | Mode verbeux | - |

## 🔎 Scan SonarCloud (`sonar.py`)

`sonar.py` reproduit le job `sonar` du workflow `quality.yml` :
1. vérifie la présence des rapports de couverture (avertit sinon),
2. lance `sonar-scanner` avec le paramétrage imposé (exclusions et chemins de couverture non configurables),
3. vérifie le Quality Gate (bloquant : code de sortie non nul si rouge),
4. exporte le rapport d'analyse (`sonar-analysis/report.json`) : Quality Gate, mesures et issues.

```bash
export SONAR_TOKEN=xxxx
python3 quality_factory/sonar.py \
  --workspace . \
  --repository owner/repo \
  --organization mon-org-sonarcloud \
  --branch main
```

| Option | Description | Défaut |
|--------|-------------|--------|
| `--workspace` | Répertoire de travail | Répertoire courant |
| `--repository` | Dépôt GitHub `owner/repo` (clé projet Sonar dérivée) | requis |
| `--organization` | Organisation SonarCloud de l'équipe | requis |
| `--host` | URL du serveur SonarCloud | `https://sonarcloud.io` |
| `--branch` | Branche analysée (dashboard + export) | `main` |
| `--coverage-dir` | Dossier des rapports de couverture | `<workspace>/coverage-artifacts` |
| `--output` | Fichier de sortie du rapport JSON | `<workspace>/sonar-analysis/report.json` |

## 📊 Format du rapport

Le rapport est généré au format JSON avec la structure suivante :

```json
{
  "status": "passed\|failed\|not_found",
  "detected": 5,
  "failed": 1,
  "failed_tests": 2,
  "frameworks": "Python (pytest src), Java (backend), Node (frontend)",
  "suites": [
    {
      "name": "Python (pytest src)",
      "status": "passed",
      "exit_code": 0,
      "tests_run": 10,
      "tests_failed": 0
    },
    {
      "name": "Java (backend)",
      "status": "failed",
      "exit_code": 1,
      "tests_run": 5,
      "tests_failed": 2
    }
  ]
}
```

## 🔍 Détection des projets

### Python
Un projet Python est détecté si :
- Il contient des fichiers de test (`test_*.py` ou `*_test.py`)
- Il contient un marqueur de projet (`pyproject.toml`, `setup.py`, `requirements.txt`, etc.)

### Java
Un projet Java est détecté si :
- Il contient un `pom.xml` (Maven) ou `build.gradle` (Gradle)
- Il contient des tests (fichiers `*Test.java` ou dans `src/test/`)
- Il n'est pas un module Maven agrégé

### Node.js
Un projet Node.js est détecté si :
- Il contient un `package.json` avec un script `test`

## ⚙️ Exécution des tests

### Python
- Installe les dépendances avec `pip install -r requirements.txt`
- Installe `pytest` et `pytest-cov`
- Exécute `pytest -q --cov --cov-report=xml:...`
- Génère un rapport de couverture au format XML (compatible SonarCloud)

### Java (Maven)
- Vérifie si JaCoCo est configuré
- Exécute `mvn verify` avec JaCoCo
- Génère un rapport JaCoCo au format XML
- Copie le rapport dans le dossier de couverture

### Java (Gradle)
- Crée un script init.gradle pour JaCoCo
- Exécute `gradle test --init-script=...`
- Génère un rapport JaCoCo au format XML

### Node.js
- Détecte le gestionnaire de paquets (pnpm > yarn > npm)
- Installe les dépendances
- Vérifie si Vitest est installé
- Si oui, exécute avec couverture LCOV
- Sinon, exécute le script test standard

## 🐳 Docker

### Build

```bash
docker build -t ghcr.io/haingue/quality_factory:latest -f quality_factory/Dockerfile .
```

### Push

```bash
docker push ghcr.io/haingue/quality_factory:latest
```

### Pull & Run

```bash
docker pull ghcr.io/haingue/quality_factory:latest
docker run -v $(pwd):/workspace quality_factory --workspace /workspace
```

## 🧪 Tests

Pour tester les scripts manuellement :

```bash
# Créer un projet de test
mkdir -p /tmp/test_project
cd /tmp/test_project

# Créer un projet Python simple
mkdir -p python_project
echo 'def test_example(): assert True' > python_project/test_example.py
echo 'pytest' > python_project/requirements.txt

# Créer un projet Node simple
mkdir -p node_project
echo '{"scripts": {"test": "echo test"}}' > node_project/package.json

# Exécuter Quality Factory
python3 /chemin/vers/quality_factory/tests.py --workspace /tmp/test_project --dry-run
```

## 📝 Notes

- Les rapports de couverture sont générés dans des formats compatibles avec **SonarCloud**
- Le script est conçu pour être exécuté dans un environnement GitHub Actions
- Toutes les dépendances (Java, Node, Python) sont optionnelles et détectées dynamiquement
- En cas d'erreur, le script continue l'exécution des autres tests

## 🔗 Liens utiles

- [Nuit de l'Info 2026](https://github.com/Haingue/nuitdelinfo2026)
- [SonarCloud](https://sonarcloud.io)
- [JaCoCo](https://www.jacoco.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Vitest](https://vitest.dev/)
