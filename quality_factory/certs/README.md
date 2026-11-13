# Certificats CA supplémentaires (optionnel)

Ce dossier permet de builder l'image **derrière un proxy d'entreprise avec
inspection TLS** (Zscaler, Prisma Access, etc.).

Déposez ici les certificats CA de votre proxy au **format PEM avec
l'extension `.crt`** (un certificat par fichier). Ils seront ajoutés au
magasin système de l'image (`update-ca-certificates`) ainsi qu'au truststore
Java, et pris en compte par npm/pnpm et pip à l'exécution.

Pour extraire la chaîne du proxy :

```bash
echo | openssl s_client -connect nodejs.org:443 -showcerts
```

> ⚠️ Les fichiers `.crt` de ce dossier sont ignorés par git : ne commitez pas
> les certificats propres à votre organisation. Sans certificat déposé, le
> build fonctionne normalement (réseau sans interception TLS, CI GitHub…).
