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
- **Cause (la plus fréquente du défi)** : votre fichier d'appel diffère du bloc généré par le bot, **même d'un seul caractère**. Coupables classiques :
  - un éditeur a converti les apostrophes `'` en `'` (apostrophe typographique) ou les tirets ;
  - fins de ligne Windows (CRLF) au lieu de LF ;
  - une ligne supprimée/ajoutée/indentée, même un espace en fin de ligne ;
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

### ❌ `You're not authorized to access this organization` / erreur de droits sur le projet
- **Cause** : le projet Sonar n'est pas rattaché à la bonne organisation, ou le token n'a pas été créé avec le bon compte.
- **À faire** : le workflow impose l'organisation du challenge. Recréez votre token depuis le compte lié à votre repo GitHub et relancez. Si l'erreur persiste, ouvrez une issue d'entraide — le paramétrage côté organisateur est peut-être en cause.

### ❌ Échec du step « Vérifier le Quality Gate »
- **Ce n'est PAS une erreur de configuration** : c'est le fonctionnement voulu (*Jidoka* — la ligne s'arrête quand il y a un défaut). Le Quality Gate Sonar est rouge tant que qualité, couverture ou sécurité ne passent pas les seuils.
- **À faire** : ouvrez votre projet sur sonarcloud.io → consultez quelles **conditions du gate** échouent (bugs, coverage, duplications…) → corrigez, pushez : le gate repasse vert et la run redevient verte.
- ⚠️ Rappel : un gate rouge à la fin de la nuit = **−10 points** et inéligibilité. Corrigez vite !

---

## 3. Le workflow ne démarre pas du tout

- **Vérifiez** : votre fichier d'appel est bien dans **`.github/workflows/`** (orthographe exacte du dossier), l'événement déclencheur est `push` sur la branche `main` (branche par défaut = `main` ? sinon, changez la branche dans Settings ou adaptez), et le fichier a l'extension `.yml`.
- **YAML invalide** ? GitHub affiche un badge orange « Invalid workflow file » sur la run : une indentation est fausse. Recollez le bloc proprement (voir § 1).

## 4. Votre équipe n'apparaît pas sur le leaderboard

1. Êtes-vous labellisés `inscrit ✅` dans votre issue d'inscription ?
2. Avez-vous au moins une run verte/rouge du workflow ? (Le leaderboard ne liste que les équipes scannées.)
3. Le leaderboard se met à jour **toutes les 15 minutes** — patientez un cycle.
4. Vérifiez `eligible` : moins de 20 commits ou gate rouge = non éligible (affiché sur votre ligne, corrigible d'ici la fin).

---

## 🏥 Demander de l'aide

Ouvrez une issue de type `🛠️ Demande d'entraide` sur le repo du défi avec :
- le **lien de votre run** GitHub Actions (onglet Actions → votre run → copiez l'URL) ;
- le **nom exact de l'étape** qui échoue ;
- les 20 premières lignes du log de l'étape fautive.

⚠️ Ne partagez **jamais** votre `SONAR_TOKEN` dans une issue. Il est visible dans les logs ? Révoquez-le immédiatement sur SonarCloud et regénérez-le.