#!/bin/bash
# Script d'exécution pour tester Quality Factory en local

set -e

echo "=========================================="
echo "Quality Factory - Execution locale"
echo "=========================================="
echo ""

# Répertoire du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(pwd)"

echo "📁 Répertoire Quality Factory: $SCRIPT_DIR"
echo "📁 Workspace: $WORKSPACE"
echo ""

# Créer un environnement virtuel si nécessaire
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "🐍 Création de l'environnement virtuel..."
    python3 -m venv "$SCRIPT_DIR/.venv"
fi

# Activer l'environnement virtuel
source "$SCRIPT_DIR/.venv/bin/activate"

# Installer les dépendances
if [ ! -f "$SCRIPT_DIR/.venv/installed" ]; then
    echo "📦 Installation des dépendances..."
    pip install --disable-pip-version-check -r "$SCRIPT_DIR/requirements.txt"
    touch "$SCRIPT_DIR/.venv/installed"
fi

echo ""
echo "⚙️  Exécution de Quality Factory..."
echo ""

# Exécuter le script principal
python3 "$SCRIPT_DIR/main.py" \
    --workspace "$WORKSPACE" \
    --coverage-dir "$WORKSPACE/coverage-artifacts" \
    --results-file "$WORKSPACE/test-results.json" \
    --temp-dir /tmp \
    --verbose \
    "$@"

# Désactiver l'environnement virtuel (optionnel)
# deactivate

echo ""
echo "✅ Fin de l'exécution"
