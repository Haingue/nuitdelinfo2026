# 🚀 Quick Start - Quality Factory

## TL;DR

Pour tester **immédiatement** les scripts sans conteneur :

```bash
# 1. Aller dans ton projet
cd /chemin/vers/ton/projet

# 2. Exécuter Quality Factory en mode dry-run (détection seulement)
python3 /chemin/vers/quality_factory/main.py --workspace . --dry-run

# 3. Exécuter avec tests réels
python3 /chemin/vers/quality_factory/main.py --workspace .

# 4. Voir les résultats
cat test-results.json
```

---

## 📋 Commandes utiles

### Mode détection uniquement (sans exécuter les tests)
```bash
python3 quality_factory/main.py --workspace . --dry-run
```

### Exécution complète avec logs détaillés
```bash
python3 quality_factory/main.py --workspace . --verbose
```

### Spécifier un dossier de couverture personnalisé
```bash
python3 quality_factory/main.py \
    --workspace . \
    --coverage-dir ./mon_dossier_couverture \
    --results-file ./mon_rapport.json
```

---

## 🧪 Test avec un projet d'exemple

### Créer un projet de test

```bash
# Créer la structure
mkdir -p /tmp/test_quality_factory
cd /tmp/test_quality_factory

# Projet Python
mkdir -p python_app
echo 'def test_example(): assert True' > python_app/test_example.py
echo 'pytest' > python_app/requirements.txt

# Projet Node
mkdir -p node_app
echo '{"name": "test", "scripts": {"test": "echo \"Tests passed\""}}' > node_app/package.json

# Projet Java (Maven)
mkdir -p java_app/src/test/java/com/example
cat > java_app/pom.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project>
    <groupId>com.example</groupId>
    <artifactId>test</artifactId>
    <version>1.0</version>
    <properties>
        <maven.compiler.source>21</maven.compiler.source>
        <maven.compiler.target>21</maven.compiler.target>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter-api</artifactId>
            <version>5.10.0</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
EOF
echo 'package com.example; public class ExampleTest { public void test() {} }' > java_app/src/test/java/com/example/ExampleTest.java
```

### Exécuter Quality Factory

```bash
# Depuis le repo nuitdelinfo2026
python3 quality_factory/main.py --workspace /tmp/test_quality_factory --dry-run

# Si tout est bon, exécuter les tests
python3 quality_factory/main.py --workspace /tmp/test_quality_factory
```

---

## 🐍 Prérequis pour le développement local

Pour tester **tous** les langages, tu as besoin de :

### Python (obligatoire)
```bash
# Vérifier la version
python3 --version  # Doit être >= 3.11

# Installer les dépendances
pip install pytest pytest-cov
```

### Java (pour les projets Java)
```bash
java -version  # Doit être >= 21
mvn -version   # Maven doit être installé
```

### Node.js (pour les projets Node)
```bash
node --version  # Doit être >= 20
npm --version   # npm doit être installé
```

---

## 📊 Que faire si ça ne marche pas ?

### Erreur: "Python non trouvé"
→ Installe Python 3.11+ et vérifie qu'il est dans ton PATH

### Erreur: "Maven non trouvé" pour un projet Java
→ Le script détecte automatiquement `mvnw` ou `mvn`. Si tu utilises `mvnw`, assure-toi qu'il est exécutable :
```bash
chmod +x java_app/mvnw
```

### Erreur: "npm non trouvé" pour un projet Node
→ Installe Node.js 20+ ou assure-toi que npm est dans ton PATH

### Le script est trop lent
→ Le timeout par défaut est de 300 secondes (5 minutes). Tu peux modifier le code dans les runners.

---

## 🔧 Dépannage

### Voir les logs détaillés
```bash
python3 quality_factory/main.py --workspace . --verbose
```

### Tester uniquement la détection
```bash
python3 quality_factory/main.py --workspace . --dry-run --verbose
```

### Vérifier les imports
```bash
cd quality_factory
python3 -c "from main import main; print('OK')"
```

---

## 📚 Prochaines étapes

1. **Teste les scripts** avec ton propre projet
2. **Vérifie les rapports** générés dans `test-results.json` et `coverage-artifacts/`
3. **Build le conteneur** quand tu es prêt :
   ```bash
   docker build -t quality_factory -f quality_factory/Dockerfile .
   ```
4. **Intègre dans le workflow** une fois que tout fonctionne

---

## 💡 Astuces

- **Pour ignorer un projet** : Ajoute un fichier `.qualityfactoryignore` dans le dossier
- **Pour forcer un langage** : Le script détecte automatiquement, mais tu peux modifier les fonctions de détection
- **Pour ajouter un nouveau langage** : Crée un nouveau fichier dans `detect/` et `runners/`

---

## 📞 Support

Si tu as des questions ou des problèmes :
- Vérifie d'abord les logs avec `--verbose`
- Consulte le README.md pour plus de détails
- Regarde le code source des runners pour comprendre la logique
