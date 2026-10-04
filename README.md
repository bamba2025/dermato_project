# Derma AI

Monorepo mobile iOS/Android d’analyse et de suivi de la peau. Cette livraison couvre
le **socle de phase 1** : React Native bare TypeScript avec projets natifs complets,
FastAPI, identité, migrations PostgreSQL/pgvector, Redis/RQ et MinIO privé.
Les phases suivantes attendent la validation des builds natifs, conformément au
[cahier des charges](docs/cahier-des-charges.md). Aucune analyse médicale active.

## Démarrer les services

Prérequis : Python 3.10+ et Docker avec Compose v2, configuré pour les conteneurs Linux.
Sous Windows, Docker Desktop nécessite un environnement WSL2 fonctionnel.

```powershell
cd C:\Users\LENOVO\Desktop\projet_dermato
python scripts/init_env.py
docker compose up --build --wait --wait-timeout 240
python scripts/smoke.py
docker compose exec -T backend python -m app.platform_probe
```

Si `.env` existe déjà, ne pas relancer sa génération : le script refuse de l’écraser.
Alternative PowerShell : `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/init-env.ps1`.
Les secrets sont aléatoires et ne sont pas affichés. `.env.example` décrit les variables.
Les services `migrate` et `storage-init` préparent la base et le bucket avant l’API.

Les images MinIO et son client sont construites localement à partir des binaires
des releases GitHub officielles fixées dans `docker/minio.Dockerfile`, car les images
précompilées configurées ne sont plus téléchargeables. Chaque téléchargement est
vérifié par SHA-256 et signature Minisign. Le premier build peut prendre plusieurs
minutes ; les builds suivants utilisent le cache Docker.

- API : http://127.0.0.1:8000 ; Swagger/OpenAPI : http://127.0.0.1:8000/docs.
- Santé : `/health/live` et `/health/ready` (base migrée, Redis, bucket).
- MinIO console : http://127.0.0.1:9001 ; identifiants dans votre `.env` local.
- Seed facultatif : `docker compose exec backend python -m app.seed`.
  Comptes fictifs : `patient@example.com`, `dermatologue@example.com` ;
  mot de passe `SEED_PASSWORD` dans `.env`, jamais codé dans le dépôt.
- Arrêt sans supprimer les données : `docker compose down`.

Les services SQL/Redis ne sont pas exposés sur le réseau hôte. Le worker fonctionne
en CPU et ne charge aucun modèle dans cette phase. MinIO conserve les objets hors SQL.

## Application mobile

Node 20.19.4+ (22.20.0 utilisé ici), JDK 17, Android SDK 36, build-tools 36.0.0,
NDK 27.1.12297006 et un appareil/émulateur Android. Pour iOS : Mac avec Xcode
compatible React Native 0.81, Ruby/Bundler et CocoaPods.

Un runtime Node portable peut être préparé dans `.tools` :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup-node.ps1
$env:Path = "$PWD\.tools\node-v22.20.0-win-x64;" + $env:Path
cd mobile
npm ci
adb reverse tcp:8000 tcp:8000
npm run android
```

Lancer Metro avec `npm start` dans un autre terminal si nécessaire. `adb reverse`
permet à l'application Android d'accéder à l'API locale liée à loopback, sans exposer
les services au Wi-Fi. Le simulateur iOS utilise directement localhost.

Sur Mac : `cd mobile`, `npm ci`, `bundle install`,
`bundle exec pod install --project-directory=ios`, puis `npm run ios`.

L’application propose inscription, consentement d’utilisation, connexion et espace
de compte. Le refresh token est conservé dans Keychain/Keystore ; l'access token
reste en mémoire. Modifier `mobile/src/config.ts` pour l'endpoint HTTPS de production.
La valeur `.invalid` bloque volontairement les appels d'un build de production
non configuré. Les releases Android sont non signées ; aucun keystore n'est livré.

## Vérifier le code

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e './backend[dev]'
.\.venv\Scripts\ruff.exe check backend/app backend/migrations backend/tests worker scripts
.\.venv\Scripts\ruff.exe format --check backend/app backend/migrations backend/tests worker scripts
.\.venv\Scripts\python.exe -m mypy --config-file backend/pyproject.toml backend/app
cd backend
..\.venv\Scripts\python.exe -m pytest -q
cd ..
.\.venv\Scripts\python.exe -m build backend --outdir backend/dist
.\.venv\Scripts\python.exe scripts/export_openapi.py
cd mobile
npm run typecheck
npm run lint
npm test -- --runInBand
npm run bundle:android
npm run bundle:ios
```

Les bundles Metro ne remplacent pas une compilation native.
Build Android : `cd mobile/android`, puis `./gradlew :app:assembleDebug`
(ou `gradlew.bat :app:assembleDebug` sous Windows).
Build iOS simulateur : suivre le job `ios` dans `.github/workflows/ci.yml` sur Mac.
La CI fournie couvre tests/lint/types/build Python, smoke Compose, tests/types/bundles
mobiles et compilations natives Android/iOS. Elle n'a pas été exécutée à distance.

## Organisation et suite

`backend/` API et migrations ; `mobile/` app et projets natifs ; `worker/` file RQ ;
`docker/` image backend ; `database/` notes SQL ; `infrastructure/` notes exploitation ;
`ml/` et `dermatologist-web/` emplacements documentés pour les phases ultérieures.

Consulter [les résultats réels et blocages](docs/status.md),
[l’architecture et ses limites](docs/architecture.md) et
[les critères de passage entre phases](docs/roadmap.md).
Caméra, pipeline qualité/IA, produits, suivi et portail dermatologue restent à réaliser.
Le socle n’est pas prêt pour des données de santé réelles ou un déploiement public.

Références techniques : [React Native bare](https://reactnative.dev/docs/0.81/getting-started-without-a-framework),
[modèle officiel](https://github.com/react-native-community/template),
[authentification FastAPI](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/).
