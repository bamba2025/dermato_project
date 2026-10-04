# Base de données

PostgreSQL 16 avec extension pgvector, activée par Alembic. Source des migrations :
`backend/migrations`. Première migration : users, user_profiles, consents,
refresh_tokens et audit_logs. UUID publics et suppression en cascade pour l'identité.

Les tables scans/images/qualité seront ajoutées en phase 2 ; analyses/versioning
en phase 3 ; questionnaires/profils cutanés en phase 4 ; produits/recommandations
en phase 5 ; dossiers/annotations en phase 6. Les migrations versionnées remplacent
la création automatique des tables au démarrage.
