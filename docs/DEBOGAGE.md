# 🛠️ Guide de dépannage — TPS Challenge

> Votre run GitHub Actions est rouge ? Ce guide couvre 95 % des erreurs. Trouvez votre message d'erreur ci-dessous et suivez la marche à suivre. Si rien ne marche, ouvrez une issue d'**entraide** sur le repo du défi avec le lien de votre run.

## Comment lire votre run

Ouvrez l'onglet **Actions** de votre repo → cliquez sur la run `TPS Challenge — Appel de l'usine qualité` → le job rouge vous indique l'étape fautive. Le **résumé de run** (en haut de page) affiche le tableau « 🏭 Rapport d'usine » avec le statut de chaque contrôle.

---

## 1. Job « Jidoka — Contrôle de conformité »

### ❌ `Aucun fichier d'inscription trouvé pour l'équipe 'X' (teams/….yml)`

- **Cause** : votre équipe n'est pas (encore) inscrite, ou le nom d'équipe de votre fichier d'appel ne correspond pas exactement à celui de l'issue d'inscription.
- **À faire** : vérifiez dans l'issue d'inscription que vous avez reçu le commentaire « ✅ Inscription validée ». Si ce n'est pas le cas, le bot a refusé votre inscription (lisez son commentaire : repo privé, nom déjà pris…). Le `team-name` dans votre fichier d'appel doit être **identique caractère pour caractère** à celui de l'issue.

### ❌ `Empreinte d'identité invalide pour cette équipe`

- **Cause** : le `identity-hash` de votre fichier d'appel ne correspond pas à celui qui vous a été attribué. Vous avez probablement copié le bloc d'une **autre équipe**, ou modifié la valeur.
- **À faire** : récupérez votre propre bloc dans le commentaire du bot de **votre** issue d'inscription et recollez-le tel quel.

### ❌ `Fichier d'appel non conforme au fichier généré lors de votre inscription`

- **Cause (la plus fréquente du défi)** : votre fichier d'appel diffère du bloc généré par le bot, **même d'un seul caractère**. Bonne nouvelle : les fins de ligne Windows (CRLF) et les espaces en fin de ligne sont **automatiquement ignorés** par le contrôle. Coupables restants :
  - un éditeur a converti les apostrophes `'` en `'` (apostrophe typographique) ou modifié les tirets/accents ;
  - une ligne supprimée/ajoutée/indentée, un caractère modifié ;
  - vous avez copié depuis un rendu Markdown qui a avalé des retours à la ligne.
- **À faire** :
  1. Supprimez le fichier `.github/workflows/appeler-tps-challenge.yml`.
  2. Sur la page GitHub de votre issue d'inscription, cliquez sur **Raw** du bloc `yaml` (ou utilisez le bouton de copie du bloc de code).
  3. Créez le fichier **directement via l'interface web GitHub** (Add file → New file) et collez le bloc — l'interface web garantit des fins de ligne LF.
  4. Commitez et relancez.
- **Vérification rapide en local** (optionnel) :
  ```bash
  sha256sum .github/workflows/appeler-tps-challenge.yml
  ```
  et comparez avec le hash du bloc d'appel — seul le bot fournit la référence ; en cas de doute, rouvrez une issue d'entraide.

### ❌ `Le repository doit être public`

- **À faire** : Settings → General → tout en bas, *Danger Zone* → *Change visibility* → Public. Relancez ensuite le workflow (onglet Actions → sélectionnez la run → *Re-run all jobs*).

---

## 2. Job « Scan qualité SonarCloud »

### ❌ Échec du step « Scanner le projet » avec `Authentication failed` / `401`

- **Cause** : le secret `SONAR_TOKEN` est absent, expiré, ou n'a pas les droits sur le projet.
- **À faire** : sur sonarcloud.io → *Mon compte → Sécurité* → générez un token (*Analyze projects*) → dans votre repo GitHub : Settings → Secrets and variables → Actions → New repository secret → nom **`SONAR_TOKEN`** (exactement, en majuscules). Relancez.

### ❌ `You are running CI analysis while Automatic Analysis is enabled`

- **Cause** : à l'import de votre repo, SonarCloud active par défaut son propre scan automatique (« Automatic Analysis »). Il entre en conflit avec le scan lancé par le workflow Toyota.
- **À faire** : sur sonarcloud.io → votre projet → **Administration → Analysis Method** → **désactivez « Automatic Analysis »** → relancez la run. Le workflow Toyota devient l'unique méthode d'analyse.

### ❌ `You're not authorized to access this organization` / `project not found` au scan

- **Cause** : la clé d'organisation SonarCloud enregistrée à votre inscription est incorrecte. Rappel : la clé d'org SonarCloud **n'est pas forcément votre login GitHub** (SonarCloud peut utiliser le display name — ex. login `Haingue` → org `FabienH`), et c'est le **propriétaire du repo** qui fait l'import.
- **À faire** : ouvrez votre projet sur sonarcloud.io et recopiez la clé d'org depuis l'URL (`sonarcloud.io/VOTRE-CLE`). Si elle diffère de celle déclarée dans votre issue d'inscription, ouvrez une issue d'entraide pour la faire corriger — le fichier d'appel sera régénéré.
- Si la clé est correcte : vérifiez que l'import a été fait **depuis le compte propriétaire du repo** et générez le token depuis ce même compte.

### ❌ Échec du step « Vérifier le Quality Gate »

- **Ce n'est PAS une erreur de configuration** : c'est le fonctionnement voulu (*Jidoka* — la ligne s'arrête quand il y a un défaut). Le Quality Gate Sonar est rouge tant que qualité, couverture ou sécurité ne passent pas les seuils.
- **À faire** : ouvrez votre projet sur sonarcloud.io → consultez quelles **conditions du gate** échouent (bugs, coverage, duplications…) → corrigez, pushez : le gate repasse vert et la run redevient verte.
- ⚠️ Rappel : un gate rouge à la fin de la nuit = **−10 points** et inéligibilité. Corrigez vite !

---

## 3. Job « Supply chain — audit dépendances » (Trivy)

### ❌ `remote Maven repository returned 429 Too Many Requests ... Retry-After: 1800`

**Cause** : Trivy tente de résoudre l'arbre transitif de vos dépendances en interrogeant Maven Central. Les runners GitHub Actions partagent des IPs, très largement rate-limitées — surtout pendant la Nuit de l'Info. Ce n'est **pas un problème dans votre repo**.

**Correction** : rien à faire — le workflow Toyota scanne en mode *offline* (`--offline-scan`), qui interdit tout appel réseau vers les registres distants. Si vous voyez encore cette erreur, vérifiez que votre fichier d'appel est bien à jour (régénérez-le depuis l'issue d'entraide si besoin). Trivy analyse quand même vos `pom.xml`, `package-lock.json`, `requirements.txt` locaux : seules les dépendances transitives non déclarées dans ces fichiers peuvent être manquées.

## 4. Le workflow ne démarre pas du tout

- **Vérifiez** : votre fichier d'appel est bien dans **`.github/workflows/`** (orthographe exacte du dossier), l'événement déclencheur est `push` sur la branche `main` (branche par défaut = `main` ? sinon, changez la branche dans Settings ou adaptez), et le fichier a l'extension `.yml`.
- **YAML invalide** ? GitHub affiche un badge orange « Invalid workflow file » sur la run : une indentation est fausse. Recollez le bloc proprement (voir § 1).

## 5. Votre équipe n'apparaît pas sur le leaderboard

1. Êtes-vous labellisés `inscrit ✅` dans votre issue d'inscription ?
2. Avez-vous au moins une run verte/rouge du workflow ? (Le leaderboard ne liste que les équipes scannées.)
3. Le leaderboard se met à jour **toutes les 15 minutes** — patientez un cycle.
4. Vérifiez `eligible` : moins de 20 commits ou gate rouge = non éligible (affiché sur votre ligne, corrigible d'ici la fin).

---

## 🏥 Demander de l'aide

Ouvrez une issue sur le repo du défi avec :

- le **lien de votre run** GitHub Actions (onglet Actions → votre run → copiez l'URL) ;
- le **nom exact de l'étape** qui échoue ;
- les 20 premières lignes du log de l'étape fautive.

⚠️ Ne partagez **jamais** votre `SONAR_TOKEN` dans une issue. Il est visible dans les logs ? Révoquez-le immédiatement sur SonarCloud et regénérez-le.