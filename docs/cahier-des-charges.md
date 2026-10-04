# PROJET : APPLICATION MOBILE D’ANALYSE ET DE SUIVI DE LA PEAU PAR IA

## 1. Objectif

Construire une application mobile iOS + Android permettant à un utilisateur de :

1. créer un profil cutané simple ;
2. photographier une zone de sa peau avec un système de capture guidée haute qualité ;
3. contrôler automatiquement la qualité de l’image AVANT son analyse ;
4. analyser les caractéristiques visibles de la peau par intelligence artificielle ;
5. combiner l’image et un questionnaire court ;
6. générer une analyse structurée avec niveau d’incertitude ;
7. recommander des produits cosmétiques compatibles avec le profil de l’utilisateur ;
8. mémoriser les produits déjà utilisés et leur tolérance ;
9. suivre l’évolution de la peau dans le temps ;
10. transmettre les cas complexes ou incertains à un dermatologue partenaire ;
11. permettre aux dermatologues d’annoter les cas afin de constituer progressivement une base dermatologique, notamment adaptée aux peaux africaines et à la population sénégalaise.

IMPORTANT :

Le MVP ne doit pas présenter les sorties de l’IA comme un diagnostic médical définitif.

Utiliser les termes :

- analyse de peau ;
- caractéristiques observées ;
- orientation possible ;
- hypothèses ;
- niveau de confiance ;
- avis dermatologique recommandé.

Un diagnostic médical confirmé doit être associé à un dermatologue.

---

# 2. Architecture globale

Construire un monorepo :

```text
derma-ai/
│
├── mobile/
│   ├── src/
│   ├── android/
│   └── ios/
│
├── dermatologist-web/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── core/
│   └── tests/
│
├── ml/
│   ├── quality/
│   ├── preprocessing/
│   ├── segmentation/
│   ├── embeddings/
│   ├── classifiers/
│   ├── uncertainty/
│   ├── inference/
│   └── training/
│
├── worker/
├── database/
├── infrastructure/
├── docker/
├── docs/
└── README.md
```

Architecture :

```text
                  ┌─────────────────┐
                  │ Application     │
                  │ mobile          │
                  └────────┬────────┘
                           │
                    HTTPS / REST
                           │
                  ┌────────▼────────┐
                  │ FastAPI Backend │
                  └────────┬────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
   PostgreSQL        Object Storage        Redis
   + pgvector          images             queue
         │                 │                 │
         │                 └───────┬─────────┘
         │                         │
         │                    AI Worker GPU
         │                         │
         │              ┌──────────▼──────────┐
         │              │ Image Quality       │
         │              ├─────────────────────┤
         │              │ Pre-processing      │
         │              ├─────────────────────┤
         │              │ ROI / segmentation  │
         │              ├─────────────────────┤
         │              │ MedSigLIP           │
         │              ├─────────────────────┤
         │              │ Classifiers         │
         │              ├─────────────────────┤
         │              │ Uncertainty / OOD   │
         │              └──────────┬──────────┘
         │                         │
         └──────────────┬──────────┘
                        ▼
               Decision / Triage Engine
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
     Recommendation           Dermatologist
        Engine                  Portal
```

---

# 3. Technologies recommandées

## Mobile

Utiliser :

```text
React Native TypeScript
```

en mode natif/bare.

Ne pas dépendre uniquement d’une bibliothèque caméra JavaScript générique.

Créer un module caméra natif spécifique :

```text
Android -> Kotlin + CameraX / Camera2
iOS     -> Swift + AVFoundation
```

React Native gère :

- navigation ;
- écrans ;
- formulaires ;
- profil ;
- historique ;
- recommandations ;
- communication API.

Kotlin/Swift gèrent la capture dermatologique.

---

# 4. Module caméra : priorité absolue

L’objectif est que la différence entre un Samsung d’entrée de gamme, un Pixel, un Xiaomi ou un iPhone influence le moins possible l’analyse.

Utiliser uniquement par défaut :

```text
caméra arrière principale
objectif 1x
pas de caméra selfie
pas de filtre beauté
pas de filtre couleur
pas de zoom numérique
```

La photo envoyée à l’IA ne doit PAS être une capture du preview.

Toujours utiliser la véritable API de capture photo haute résolution du smartphone.

---

# 5. Android Camera

Utiliser CameraX avec :

```text
ImageCapture.CAPTURE_MODE_MAXIMIZE_QUALITY
```

et :

```text
JPEG quality = 100
```

Choisir la résolution photo la plus élevée raisonnablement disponible sur le capteur principal.

Le preview peut être inférieur en résolution.

Le pipeline Android doit utiliser simultanément :

```text
Preview
+
ImageAnalysis
+
ImageCapture
```

`ImageAnalysis` permet d’analyser le flux vidéo en temps réel.

`ImageCapture` réalise la photo finale haute résolution.

Activer les fonctions 3A :

```text
AF = autofocus
AE = auto exposure
AWB = auto white balance
```

Attendre leur stabilisation avant capture.

---

# 6. iPhone Camera

Utiliser :

```text
AVFoundation
AVCaptureSession
AVCapturePhotoOutput
```

Configurer :

```text
photoQualityPrioritization = .quality
```

et utiliser les dimensions photo maximales adaptées au capteur.

Utiliser la caméra :

```text
builtInWideAngleCamera
position = back
```

Ne pas utiliser de filtre ou de transformation esthétique.

---

# 7. Format d’image

Pour le pipeline IA standard :

```text
JPEG SDR haute qualité
profil couleur sRGB
```

Conserver l’original haute résolution.

Créer séparément une image normalisée destinée à l’IA.

Ne pas remplacer l’original.

Structure :

```text
scan/
   original.jpg
   standardized.jpg
   roi.jpg
   thumbnail.jpg
```

Le RAW peut être supporté ultérieurement en mode recherche, mais il ne doit pas être nécessaire pour le MVP.

---

# 8. Système de capture guidée

L’utilisateur ne doit pas simplement voir un bouton photo.

Afficher une interface temps réel :

```text
        ┌─────────────────────────┐
        │                         │
        │       zone peau         │
        │        ┌─────┐          │
        │        │     │          │
        │        └─────┘          │
        │                         │
        │  ✓ Lumière correcte     │
        │  ✓ Mise au point        │
        │  ✓ Distance correcte    │
        │  ✓ Téléphone stable     │
        │                         │
        │       [ PHOTO ]         │
        └─────────────────────────┘
```

Le bouton de capture devient actif lorsque les conditions sont suffisamment bonnes.

---

# 9. Image Quality Gate en temps réel

Analyser environ 5 à 10 images du preview par seconde.

Créer :

```text
ImageQualityAnalyzer
```

Il doit calculer au minimum :

```text
sharpness_score
blur_score
brightness_score
underexposure_score
overexposure_score
glare_score
shadow_score
contrast_score
motion_score
framing_score
distance_score
resolution_score
color_cast_score
```

Retour :

```json
{
  "quality_score": 0.91,
  "sharpness": 0.94,
  "lighting": 0.88,
  "glare": 0.04,
  "motion": 0.02,
  "distance": 0.93,
  "capture_allowed": true,
  "instructions": []
}
```

Si mauvaise qualité :

```text
Photo trop sombre
Rapprochez-vous
Éloignez légèrement le téléphone
Stabilisez le téléphone
Évitez le reflet lumineux
Nettoyez l’objectif
Touchez la zone pour effectuer la mise au point
Placez la zone au centre
```

Tous les seuils doivent se trouver dans un fichier de configuration.

Ne pas coder les seuils directement dans les composants.

Exemple :

```text
config/image_quality.yaml
```

Les seuils initiaux sont des paramètres de développement et devront être recalibrés avec les données réelles.

---

# 10. Détection du flou

Implémenter initialement plusieurs indicateurs :

```text
Variance of Laplacian
Tenengrad gradient
local contrast
edge density
```

Ne pas utiliser uniquement la variance du Laplacien.

Combiner les indicateurs dans un score normalisé.

Plus tard permettre de remplacer ce module par un petit CNN/MobileNet entraîné spécifiquement pour la qualité des photographies dermatologiques.

Architecture :

```text
QualityAnalyzerInterface
     │
     ├── ClassicalQualityAnalyzer
     │
     └── NeuralQualityAnalyzer
```

---

# 11. Détection de mouvement

Utiliser :

- données gyroscope/accéléromètre ;
- différence entre frames ;
- éventuellement optical flow.

Si mouvement trop important :

```text
"Stabilisez le téléphone"
```

Ne capturer automatiquement qu’après quelques centaines de millisecondes de stabilité.

---

# 12. Gestion de la lumière

Détecter :

- sous-exposition ;
- surexposition ;
- zones brûlées ;
- ombres très importantes ;
- reflets spéculaires.

Ne pas utiliser le flash automatiquement.

Si lumière insuffisante :

```text
"Placez-vous dans une zone mieux éclairée."
```

Privilégier une lumière naturelle ou diffuse.

---

# 13. Couleur de peau et différences entre smartphones

Créer deux images :

```text
ORIGINAL
NORMALIZED
```

ORIGINAL :

image sortie directement de la caméra.

NORMALIZED :

- correction d’orientation ;
- conversion sRGB ;
- normalisation très limitée ;
- correction de balance des blancs si nécessaire ;
- color constancy contrôlée.

IMPORTANT :

Ne jamais appliquer une correction agressive qui pourrait effacer :

- rougeurs ;
- pigmentation ;
- coloration ;
- contraste lésion/peau.

L’IA doit pouvoir accéder à l’image originale ET à la version normalisée.

En production :

```text
inference(original, normalized)
```

ou utiliser la version qui aura donné les meilleurs résultats lors de la validation.

---

# 14. Mode clinique avec carte de calibration

Prévoir dès l’architecture un mode :

```text
ClinicalCaptureMode
```

destiné aux dermatologues partenaires et à la constitution du dataset.

Possibilité de mettre dans l’image une petite carte contenant :

- références de couleur ;
- gris neutre ;
- échelle millimétrique.

Le logiciel peut détecter automatiquement la carte.

Elle permettra :

```text
color calibration
+
measurement calibration
+
device normalization
```

Cette fonctionnalité est facultative pour l’utilisateur normal mais fortement recommandée pour les images servant à entraîner ou valider les futurs modèles.

---

# 15. Protocole de prise de vue

Pour chaque problème cutané, guider l’utilisateur vers 3 photographies :

### Photo 1 — Contexte

Zone du corps suffisamment large.

Exemple :

```text
avant-bras complet
```

### Photo 2 — Intermédiaire

La zone concernée occupe environ une part importante de l’écran.

### Photo 3 — Gros plan

Permet de voir :

- texture ;
- bordures ;
- squames ;
- boutons ;
- pigmentation ;
- surface de la lésion.

Enregistrer :

```text
CONTEXT
MID_RANGE
CLOSE_UP
```

Les 3 images appartiennent au même :

```text
scan_session_id
```

---

# 16. Métadonnées caméra

Enregistrer uniquement les métadonnées nécessaires à l’amélioration de l’IA :

```text
manufacturer
device_model
camera_id
image_width
image_height
ISO
exposure_time
focal_length
aperture
orientation
flash_used
timestamp
app_version
camera_module_version
```

Supprimer :

```text
GPS latitude
GPS longitude
exact user location
```

des EXIF avant stockage.

---

# 17. Pipeline serveur de qualité

Après upload, effectuer une deuxième validation :

```text
Mobile quality gate
        ↓
Upload original
        ↓
Server quality gate
        ↓
Accepted / Rejected
```

Si serveur refuse :

```text
analysis_status = RECAPTURE_REQUIRED
```

et expliquer précisément pourquoi.

---

# 18. Pipeline IA principal

Architecture :

```text
Images
   ↓
Quality validation
   ↓
Orientation / sRGB
   ↓
ROI extraction
   ↓
Medical vision encoder
   ↓
MedSigLIP
   ↓
Embeddings
   ↓
Task-specific classifiers
   ↓
Calibration
   ↓
OOD detection
   ↓
Uncertainty
   ↓
Decision engine
```

---

# 19. Modèle principal

Utiliser comme modèle principal de production :

```text
google/medsiglip-448
```

MedSigLIP devient le :

```text
VisionBackbone
```

Architecture logicielle :

```python
class VisionBackbone:
    def encode(image):
        pass
```

Implémentations :

```text
MedSigLIPBackbone
MockBackbone
ExperimentalBackbone
```

Cela doit permettre de changer de modèle sans modifier le reste de l’application.

---

# 20. Important : ne pas utiliser MedSigLIP directement comme diagnostic final

MedSigLIP produit des représentations/embeddings.

Créer au-dessus des embeddings des modèles spécifiques.

Exemple :

```text
MedSigLIP
   ↓
Embedding
   ├── image quality classifier
   ├── visual signs classifier
   ├── dermatological condition classifier
   ├── severity classifier
   └── out-of-distribution detector
```

---

# 21. Premier modèle : signes visuels

Le premier modèle à entraîner doit chercher des caractéristiques observables et non uniquement des maladies.

Sorties potentielles :

```text
dryness
redness
hyperpigmentation
hypopigmentation
papules
pustules
comedones
scaling
crusting
erosion
ulceration
plaques
nodules
vesicles
roughness
swelling
```

Format :

```json
{
  "dryness": {
    "probability": 0.86,
    "severity": "moderate"
  },
  "redness": {
    "probability": 0.41,
    "severity": "mild"
  },
  "hyperpigmentation": {
    "probability": 0.73,
    "severity": "moderate"
  }
}
```

---

# 22. Modèle pathologies

Créer un modèle multilabel différent du modèle de signes visuels.

Il pourra évoluer progressivement.

Exemples futurs :

```text
acne
eczema
contact dermatitis
atopic dermatitis
fungal infection
psoriasis
folliculitis
urticaria
etc.
```

MAIS l’interface utilisateur doit présenter :

```text
Possibilités à considérer
```

et non :

```text
Vous avez ...
```

tant que le modèle n’a pas fait l’objet d’une validation clinique adaptée.

---

# 23. Gestion de l’incertitude

Créer :

```text
UncertaintyService
```

L’IA doit être capable de répondre :

```text
JE NE SAIS PAS
```

Cela est obligatoire.

Calculer :

```text
classification confidence
calibrated probability
embedding distance
out-of-distribution score
image quality score
```

Utiliser notamment :

```text
temperature scaling
```

sur un dataset de validation.

Créer ensuite :

```text
confidence_level =
HIGH
MEDIUM
LOW
UNUSABLE
```

---

# 24. Out-of-distribution detection

Une maladie ou une image très différente des données d’entraînement ne doit pas être forcée dans une classe connue.

Utiliser les embeddings MedSigLIP.

Implémentation possible :

```text
k-NN embedding distance
+
Mahalanobis distance
+
classifier entropy
```

Retour :

```text
OOD_LOW
OOD_MEDIUM
OOD_HIGH
```

Si :

```text
OOD_HIGH
```

alors :

```text
ne pas donner d’hypothèse forte
→ proposer dermatologue
```

---

# 25. Decision Engine

Créer un moteur totalement séparé de l’IA :

```text
DecisionEngine
```

Il prend :

```text
image_quality
classifier_output
uncertainty
OOD
questionnaire
symptoms
duration
```

et retourne :

```text
COSMETIC_GUIDANCE
MONITOR
DERMATOLOGIST_RECOMMENDED
DERMATOLOGIST_PRIORITY
RECAPTURE_REQUIRED
```

Les règles doivent être configurables.

Ne jamais permettre au modèle génératif de décider seul du niveau de triage.

---

# 26. MedGemma

Ajouter facultativement :

```text
google/medgemma-1.5-4b-it
```

Son rôle :

- reformuler les résultats ;
- produire une explication compréhensible ;
- résumer le questionnaire ;
- préparer un résumé pour le dermatologue.

Il ne doit PAS remplacer les sorties déterministes du pipeline précédent.

Entrée :

```text
structured AI result
+
questionnaire
+
profile
```

Sortie :

```text
explication en langage naturel
```

Les valeurs numériques du modèle principal doivent être transmises et conservées séparément.

---

# 27. Questionnaire utilisateur

Ne pas faire un questionnaire de 30 questions.

Questionnaire principal :

```text
1. Quelle zone voulez-vous analyser ?

2. Quel est le problème principal ?
   - boutons
   - taches
   - sécheresse
   - démangeaisons
   - rougeur
   - irritation
   - autre

3. Depuis combien de temps ?

4. Ressentez-vous :
   - douleur
   - brûlure
   - démangeaison
   - aucun

5. Utilisez-vous actuellement des produits sur cette zone ?

6. Avez-vous déjà constaté une réaction à un produit ?
```

Ensuite :

```text
DynamicQuestionEngine
```

peut afficher une question supplémentaire en fonction du cas.

---

# 28. Profil cutané

Table :

```text
skin_profiles
```

Champs :

```text
id
user_id
primary_skin_concerns
sensitivity_reported
dryness_history
oiliness_history
acne_history
preferred_product_types
created_at
updated_at
```

Éviter les données inutiles.

---

# 29. Mémoire des produits

Créer :

```text
products
ingredients
product_ingredients
user_product_experiences
```

Exemple :

```text
User
   ↓
used
   ↓
Product
   ↓
contains
   ↓
Ingredients
```

`user_product_experiences` :

```text
id
user_id
product_id
body_area
started_at
stopped_at
usage_frequency
tolerance
effectiveness
itching
burning
redness
dryness
breakout
notes
```

Valeurs de tolérance :

```text
VERY_GOOD
GOOD
NEUTRAL
BAD
VERY_BAD
UNKNOWN
```

---

# 30. Base produits

Table :

```text
products
```

Champs :

```text
id
brand
name
category
barcode
description
country
image_url
fragrance_free
hypoallergenic_claim
created_at
```

Table :

```text
ingredients
```

Champs :

```text
id
inci_name
common_name
ingredient_type
notes
```

Catégories :

```text
cleanser
body_wash
soap
moisturizer
body_lotion
face_cream
sunscreen
shampoo
etc.
```

---

# 31. Moteur de recommandation cosmétique

Créer :

```text
RecommendationEngine
```

V1 doit être essentiellement :

```text
rules based
+
historique utilisateur
+
compatibilité ingrédients
```

Ne pas commencer par un gros modèle génératif.

Exemple :

```text
profile
+
skin findings
+
known tolerated products
+
known poorly tolerated products
+
ingredients
       ↓
Recommendation score
```

Retour :

```json
{
  "product_id": 15,
  "score": 0.89,
  "reasons": [
    "formulation compatible avec le profil actuel",
    "produits similaires déjà bien tolérés",
    "sans ingrédient précédemment associé à une réaction"
  ]
}
```

Important :

Une réaction à un produit ne permet pas automatiquement d’affirmer quel ingrédient l’a provoquée.

Stocker :

```text
association
```

et non :

```text
causality
```

---

# 32. Suivi longitudinal

Permettre :

```text
Scan J0
Scan J7
Scan J30
Scan J90
```

Chaque scan est relié à :

```text
skin_issue_id
```

Comparer :

```text
image embeddings
visual scores
severity
user symptoms
products used
```

Créer :

```text
ProgressTrackingService
```

Afficher :

```text
amélioration possible
stable
aggravation possible
données insuffisantes
```

---

# 33. Comparaison photographique

Pour un suivi, aider l’utilisateur à reproduire :

```text
même zone
même distance
même orientation
lumière similaire
```

Stocker les métadonnées de la capture précédente.

Afficher une silhouette/overlay de la photo précédente pour aider au repositionnement.

---

# 34. Dermatologue partenaire

Créer une application web distincte :

```text
Next.js + TypeScript
```

Authentification spécifique :

```text
DERMATOLOGIST
ADMIN
```

Dashboard :

```text
Nouveaux dossiers
Dossiers prioritaires
Dossiers en attente
Mes consultations
Dossiers terminés
```

---

# 35. Dossier dermatologue

Afficher :

```text
3 images originales
3 images normalisées
historique photographique
zone du corps
questionnaire
symptômes
produits utilisés
résultats IA
niveau de confiance
OOD score
historique utilisateur pertinent
```

L’IA doit être clairement distinguée de l’avis médical.

---

# 36. Annotation dermatologue

Le dermatologue peut saisir :

```text
primary_diagnosis
differential_diagnoses
visual_findings
severity
confidence
recommended_action
notes
```

et indiquer :

```text
AI_CORRECT
AI_PARTIALLY_CORRECT
AI_INCORRECT
AI_UNCERTAIN
```

Ces données deviennent une source d’amélioration du modèle uniquement lorsque le consentement approprié existe.

---

# 37. Dataset interne

Créer une architecture permettant d’obtenir :

```text
Image
+
Metadata
+
Questionnaire
+
AI prediction
+
Dermatologist annotation
+
Outcome
```

Ne jamais entraîner directement sur la base de production.

Construire un pipeline :

```text
production DB
      ↓
de-identification
      ↓
research dataset
      ↓
quality control
      ↓
train
validation
test
```

Séparer les patients entre train / validation / test.

Le même patient ne doit jamais apparaître dans plusieurs ensembles.

---

# 38. Modèle versioning

Créer table :

```text
model_versions
```

Champs :

```text
id
name
version
checkpoint_hash
dataset_version
training_date
metrics
status
created_at
```

Chaque analyse doit enregistrer :

```text
model_version_id
preprocessing_version
quality_model_version
decision_engine_version
```

afin qu’un résultat soit entièrement reproductible.

---

# 39. PostgreSQL + pgvector

Utiliser :

```text
PostgreSQL
+
pgvector
```

Les embeddings MedSigLIP peuvent être stockés dans pgvector.

Utilités :

```text
similar image retrieval
OOD detection
case similarity
research
longitudinal comparison
```

---

# 40. Tables principales

Créer au minimum :

```text
users
user_profiles
skin_profiles
skin_issues

scan_sessions
scan_images
image_quality_results

questionnaires
questionnaire_answers

ai_analyses
ai_findings
ai_differentials

model_versions

products
ingredients
product_ingredients
user_product_experiences
recommendations

dermatologist_profiles
dermatologist_cases
dermatologist_reviews

consents
audit_logs
```

Utiliser UUID comme identifiants publics.

---

# 41. Stockage image

Ne jamais enregistrer les images directement dans PostgreSQL.

Utiliser un stockage objet compatible S3.

Développement :

```text
MinIO
```

Production :

```text
S3-compatible secure object storage
```

Arborescence :

```text
users/{user_uuid}/scans/{scan_uuid}/original/
users/{user_uuid}/scans/{scan_uuid}/processed/
```

Utiliser des URLs signées temporaires.

---

# 42. Sécurité

Mettre en œuvre :

```text
TLS
encryption at rest
JWT access token
refresh tokens
RBAC
signed URLs
audit logs
rate limiting
```

Les images dermatologiques sont considérées comme des données sensibles.

Ne jamais rendre un bucket public.

---

# 43. Consentement

Créer :

```text
consents
```

Différencier :

```text
APPLICATION_USE
MEDICAL_REVIEW
RESEARCH_USE
AI_TRAINING
```

Un utilisateur doit pouvoir utiliser certaines fonctions sans obligatoirement accepter que ses images soient réutilisées pour entraîner l’IA.

---

# 44. Suppression des données

Prévoir :

```text
DELETE ACCOUNT
EXPORT DATA
DELETE IMAGES
REVOKE RESEARCH CONSENT
```

La suppression doit être propagée dans :

```text
database
object storage
indexes
derived files
```

selon les règles de conservation applicables.

---

# 45. API

Créer une API REST versionnée :

```text
/api/v1/
```

Principaux endpoints :

```text
POST   /auth/register
POST   /auth/login
POST   /auth/refresh

GET    /me
PATCH  /me

GET    /skin-profile
PATCH  /skin-profile

POST   /scans
GET    /scans
GET    /scans/{id}

POST   /scans/{id}/images
POST   /scans/{id}/questionnaire
POST   /scans/{id}/analyze

GET    /scans/{id}/analysis
GET    /analysis-jobs/{id}

GET    /products
GET    /products/{id}

POST   /product-experiences
PATCH  /product-experiences/{id}

GET    /recommendations

POST   /dermatologist-cases
GET    /dermatologist-cases/{id}

POST   /consents
DELETE /consents/{id}
```

Utiliser OpenAPI automatiquement via FastAPI.

---

# 46. Traitement asynchrone

L’analyse IA ne doit pas bloquer l’API HTTP.

Architecture :

```text
FastAPI
   ↓
Redis
   ↓
Worker
   ↓
GPU inference
```

Statuts :

```text
UPLOADING
QUALITY_CHECK
QUEUED
PROCESSING
COMPLETED
FAILED
RECAPTURE_REQUIRED
```

Le mobile peut utiliser :

```text
polling
```

au MVP.

Préparer ensuite WebSocket/SSE.

---

# 47. Interface mobile

Écrans minimum :

```text
Splash
Onboarding
Consent
Register/Login

Home

New Scan
Body Area
Camera Context
Camera Mid-range
Camera Close-up
Image Review
Questionnaire
Analyzing
Analysis Result

Recommendations
Product Detail
My Products

History
Scan Detail
Progress

Dermatologist
Consultation Request

Profile
Privacy
Delete Data
```

---

# 48. Écran résultat

Ne pas afficher seulement :

```text
Eczéma 92 %
```

Afficher :

```text
Analyse de votre peau

Qualité des images
Très bonne

Caractéristiques observées
• sécheresse : modérée
• pigmentation : modérée
• irritation visible : faible

Orientation
Plusieurs situations peuvent produire cet aspect.

Confiance de l’analyse
Modérée

Conseil
...

Produits compatibles
...

[ Demander l’avis d’un dermatologue ]
```

---

# 49. Cas à risque / incertains

Si :

```text
image_quality faible
OR
confidence faible
OR
OOD élevé
OR
signaux de triage configurés
```

alors :

```text
NE PAS générer de diagnostic affirmatif
```

Afficher :

```text
Cette image ne permet pas à l’IA de fournir une analyse suffisamment fiable.

Nous vous recommandons un avis dermatologique.
```

---

# 50. Architecture modèle expérimentale

Prévoir :

```text
MODEL_BACKBONE=medsiglip
```

et architecture interchangeable :

```text
medsiglip
future_commercial_model
research_only_model
```

Ne pas intégrer PanDerm ou DermFM-Zero dans un build commercial car leurs licences publiées sont actuellement non commerciales.

Ils pourront seulement servir dans des expérimentations séparées pour comparer les performances.

---

# 51. Tests IA

Évaluer les performances séparément selon :

```text
device manufacturer
device model
camera resolution
lighting condition
skin tone groups
age groups lorsque disponible
body area
condition
image quality group
```

Ne jamais fournir uniquement une précision globale.

Mesures :

```text
AUROC
AUPRC
sensitivity
specificity
precision
recall
F1
ECE calibration
Brier score
confusion matrix
```

---

# 52. Validation smartphone

Créer un benchmark interne avec plusieurs catégories :

```text
Android entrée de gamme
Android milieu de gamme
Android haut de gamme
iPhone récent
iPhone plus ancien
```

Photographier les mêmes cas/images de référence dans différentes conditions.

Objectif :

mesurer le `device domain shift`.

---

# 53. Tests couleur

En mode laboratoire/clinique, utiliser une carte couleur de référence.

Comparer :

```text
captured RGB
reference color
ΔE color difference
```

Cela permettra de quantifier les différences entre téléphones.

---

# 54. Ne pas “réparer” artificiellement une mauvaise image

Principe :

```text
RECAPTURE > IMAGE ENHANCEMENT
```

Si l’image est floue ou surexposée, demander une nouvelle photo.

Un algorithme d’amélioration ne peut pas recréer des informations médicales qui n’ont pas été capturées.

Les améliorations d’image doivent principalement servir à :

```text
normalisation
visualisation
réduction des différences de domaine
```

et doivent être validées avant d’être utilisées dans le pipeline clinique.

---

# 55. Docker

Fournir :

```text
docker-compose.yml
```

avec :

```text
backend
worker
postgres
redis
minio
```

Lancer le développement avec :

```bash
docker compose up
```

Prévoir un mode CPU lorsque GPU absent.

---

# 56. Configuration

Utiliser :

```text
.env
.env.example
```

Ne jamais coder de secret.

Variables :

```text
DATABASE_URL
REDIS_URL
S3_ENDPOINT
S3_BUCKET
JWT_SECRET
MODEL_PATH
MODEL_BACKBONE
MEDGEMMA_ENABLED
GPU_DEVICE
```

---

# 57. Mode développement sans modèle

L’application doit pouvoir fonctionner avant l’installation des modèles médicaux.

Créer :

```text
MockInferenceService
```

qui produit une réponse structurée fictive.

Cela permet de développer entièrement :

```text
mobile
backend
database
camera
product engine
dermatologist portal
```

indépendamment du GPU.

---

# 58. Monitoring

Ajouter :

```text
structured logging
request id
scan id
model version
latency
inference latency
quality rejection rate
analysis failure rate
```

Préparer OpenTelemetry.

Ne jamais logger les images ou les informations médicales sensibles en clair.

---

# 59. Tests logiciels

Créer :

```text
unit tests
integration tests
API tests
database tests
camera quality tests
ML tests
end-to-end tests
```

CI :

```text
lint
typecheck
test
build
```

---

# 60. Ordre de développement

Ne pas essayer de tout développer simultanément.

## Phase 1

Créer :

```text
monorepo
Docker
PostgreSQL
Redis
MinIO
FastAPI
React Native
authentication
database migrations
```

## Phase 2

Créer le module caméra dermatologique :

```text
CameraX Android
AVFoundation iOS
live quality gate
3-photo workflow
upload
```

Cette phase est prioritaire.

## Phase 3

Créer le pipeline IA avec :

```text
Mock model
puis MedSigLIP
```

## Phase 4

Créer :

```text
questionnaire
skin profile
analysis screen
history
```

## Phase 5

Créer :

```text
products
ingredients
product history
recommendation engine
```

## Phase 6

Créer :

```text
dermatologist portal
medical review
annotations
```

## Phase 7

Créer :

```text
training pipeline
model evaluation
local Senegalese dataset integration
calibration
OOD
fairness evaluation
```

---

# 61. Première version IA

Pour la toute première version fonctionnelle :

```text
MedSigLIP
    ↓
frozen embeddings
    ↓
small MLP / linear heads
```

Ne pas fine-tuner immédiatement l’intégralité du modèle.

Enregistrer les embeddings.

Avec davantage de données sénégalaises annotées :

```text
Phase A : linear probe
Phase B : partial fine-tuning
Phase C : full fine-tuning si bénéfice démontré
```

Comparer les performances à chaque étape.

---

# 62. Dataset sénégalais

Préparer le pipeline afin de pouvoir intégrer ultérieurement des données provenant de partenaires dermatologues sénégalais.

Chaque entrée de recherche pourra contenir :

```text
images
body area
capture metadata
questionnaire
symptoms
visual findings
diagnosis dermatologist
differential diagnosis
severity
treatment/recommendation
follow-up
products used
outcome
```

Ajouter un champ :

```text
annotation_status
```

avec :

```text
UNREVIEWED
ONE_DERM_REVIEW
TWO_DERM_CONSENSUS
ADJUDICATED
```

---

# 63. Critère majeur de réussite

Ne pas considérer le projet comme réussi uniquement parce que :

```text
photo → modèle → texte
```

Le système doit démontrer :

```text
bonne image
       ↓
analyse robuste
       ↓
incertitude connue
       ↓
profil utilisateur
       ↓
historique produits
       ↓
recommandation
       ↓
suivi
       ↓
dermatologue si nécessaire
```

---

# 64. Livrables demandés à Codex

Construire réellement le projet et fournir :

```text
1. monorepo complet ;
2. application React Native ;
3. module CameraX Android ;
4. module AVFoundation iOS ;
5. FastAPI backend ;
6. PostgreSQL schema + migrations ;
7. Redis worker ;
8. MinIO storage ;
9. image quality pipeline ;
10. interface MedSigLIP ;
11. mock inference ;
12. recommendation engine V1 ;
13. dermatologist web portal ;
14. Docker Compose ;
15. tests ;
16. .env.example ;
17. seed database ;
18. README d’installation ;
19. documentation architecture ;
20. API OpenAPI fonctionnelle.
```

Ne laisser aucune clé API ou secret dans le dépôt.

Créer un code modulaire, documenté et typé.

Ne jamais coupler directement l’interface mobile au modèle IA : toutes les inférences passent par le backend.

Le système doit rester fonctionnel si MedSigLIP est remplacé ultérieurement par un meilleur modèle.

Commencer par Phase 1 puis Phase 2. Vérifier que l’application compile et que les tests passent avant de passer à la phase suivante.