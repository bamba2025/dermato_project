# État réel — 4 octobre 2026

## Validation Docker du 4 octobre

Docker Compose Linux est désormais opérationnel sur ce poste. Les images MinIO
configurées étant introuvables, les images locales utilisent les mêmes versions
des binaires officiels GitHub, vérifiés par SHA-256 et signature Minisign.

- `docker compose up -d --build --wait --wait-timeout 180` : réussi ; PostgreSQL,
  Redis, MinIO, backend et worker sont sains. Migration et création du bucket
  terminées avec succès.
- `scripts/smoke.py` : réussi contre l'API réelle, avec un compte fictif.
- `python -m app.platform_probe` dans le backend : réussi ; extension pgvector,
  objet S3 privé, accès anonyme interdit, URL signée et tâche RQ exécutée.

Le verrou Docker de phase 1 est levé. Les validations natives Android et iOS
restent à effectuer ; ces contrôles ne valident pas l'application mobile sur
appareil. Le bilan du 3 octobre ci-dessous conserve les résultats antérieurs.

## Bilan du 3 octobre

**Phase 1 construite, validation complète bloquée par l'outillage.** Les phases 2–7
ne sont pas commencées. Le projet complet demandé n'est donc pas encore livré.

## Livré dans le socle

- React Native 0.81.0 bare, TypeScript, projets Android/Kotlin et iOS/Swift issus
  du modèle officiel ; inscription, consentement d'utilisation, connexion, compte,
  session sécurisée Keychain/Keystore, renouvellement et déconnexion.
- FastAPI `/api/v1`, OpenAPI, authentification Argon2/JWT, refresh tokens hachés
  avec rotation et détection de réutilisation, RBAC lu en base, profils isolés,
  audit minimal et limitation de débit Redis.
- Migration Alembic explicite : identité, profils, consentements séparés,
  refresh tokens et audit ; extension pgvector en PostgreSQL.
- Compose : PostgreSQL, Redis authentifié, MinIO privé, initialisation du bucket,
  migration, backend et worker RQ Linux. Son exécution n'est pas encore vérifiée.
- Secrets générés dans `.env` ignoré ; aucun keystore ou secret dans les sources.
- Tests, CI préparée, seed fictif, scripts de validation et documentation.

## Contrôles effectivement exécutés sur ce poste

Environnement : Windows, Python 3.10.7, Node portable 22.20.0.

| Contrôle | Résultat |
|---|---|
| Tests backend API/sécurité/isolation/migration SQLite | **13 passent** |
| Tests mobile client API/session et écran d'authentification | **8 passent**, 2 suites |
| Ruff lint et format Python | OK |
| Mypy avec plugin Pydantic | OK, 19 fichiers sources |
| TypeScript `tsc --noEmit` | OK |
| ESLint mobile | OK |
| Package Python wheel et sdist | Build réussi |
| Export `docs/openapi.json` | Généré depuis l'application FastAPI |
| Bundles Metro Android et iOS, mode production | Générés dans `mobile/build` |
| Syntaxe YAML Compose et CI | OK ; pas une validation de leur exécution |
| Compilation native Android | Tentée ; échec avant compilation, Java absent |
| Compilation native iOS | Non exécutée, aucun Mac/Xcode disponible |
| Smoke Compose et probe pgvector/S3/RQ | Non exécutés, Docker absent |
| CI distante | Non exécutée ; workflow fourni uniquement |

Les tests backend émettent un avertissement de dépréciation de dépendance
Starlette/AnyIO, sans échec. Les tests Jest autorisent 30 secondes pour le premier
chargement Babel sous Windows ; l'exécution finale a pris environ 3 secondes.

L'erreur Android exacte est :

```text
ERROR: JAVA_HOME is not set and no 'java' command could be found in your PATH.
```

Les bundles JavaScript ne prouvent ni la compilation native ni le fonctionnement
de Keychain/Keystore sur appareil. Les migrations SQLite ne prouvent pas les
verrous transactionnels PostgreSQL. Aucun résultat clinique n'est testé ou revendiqué.

## Reprendre la validation de phase 1

1. Fournir Docker Compose Linux opérationnel, puis lancer les commandes de
   démarrage/smoke du README et `app.platform_probe` pour vérifier réellement
   pgvector, accès S3 anonyme interdit, URL signée et traitement d'une tâche RQ.
2. Installer/configurer JDK 17 (`JAVA_HOME`) et Android SDK 36 + build-tools 36.0.0
   + NDK 27.1.12297006. Compiler `:app:assembleDebug`, puis tester inscription,
   connexion et restauration de session sur appareil/émulateur.
3. Disposer d'un Mac/Xcode ou d'un runner CI macOS. Installer les Pods, compiler
   pour le simulateur et tester la session native iOS. L'utilisateur a indiqué
   qu'il n'en dispose pas pour le moment.
4. Exécuter les jobs de `.github/workflows/ci.yml` dans un dépôt GitHub autorisé,
   ou effectuer les contrôles équivalents localement.

Après ces validations seulement, commencer la phase 2 CameraX/AVFoundation.
Caméra dermatologique, contrôle qualité, uploads de photos, inférence mock/MedSigLIP,
recommandations, suivi, portail Next.js et entraînement restent à réaliser.
`ml/` et `dermatologist-web/` sont des emplacements documentés, pas des fonctionnalités
implémentées. Export/suppression de compte, suppression des images et révocation
recherche ne sont pas encore disponibles.
