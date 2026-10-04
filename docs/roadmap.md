# Ordre de réalisation et critères d'acceptation

Respecter le verrou demandé : tests et compilation de la phase courante avant la suivante.

| Phase | Périmètre | Critère avant passage |
|---|---|---|
| 1 | Monorepo, Compose, FastAPI, PostgreSQL/pgvector, Redis, MinIO, identité, migrations, React Native bare | Tests API et migrations ; smoke sur Compose ; build Android et iOS |
| 2 | CameraX/Camera2, AVFoundation, preview + analyse + photo, 3A, qualité live, trois vues, upload privé | Compilation native ; captures physiques sur plusieurs téléphones ; serveur refuse les mauvaises images ; EXIF sans GPS |
| 3 | Mock puis backbone MedSigLIP, embeddings et têtes entraînées, asynchrone, OOD, incertitude, règles versionnées | Mock identifié ; absence d'inférence si qualité insuffisante ; incertitude sans hypothèse forte ; traçabilité |
| 4 | Questionnaire court/dynamique, profil cutané, résultat, historique, progression | Flux complet sans diagnostic définitif ; isolation des utilisateurs |
| 5 | Catalogue, INCI, expériences, recommandations à règles | Exclusion produits mal tolérés ; associations sans causalité inventée ; explications |
| 6 | Next.js dermatologue, dossiers assignés, avis, annotations | RBAC ; consentement avis ; IA séparée du diagnostic professionnel ; audit |
| 7 | Export désidentifié, données sénégalaises, entraînement, calibration, évaluation | Consentements recherche/IA ; splits patient ; métriques par sous-groupes et appareil |

La suppression/export des données et la révocation des consentements doivent être
implémentés et testés avant l'utilisation de données de santé réelles. Ces fonctions
ne sont pas disponibles dans le socle d'identité actuel.
