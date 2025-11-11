## Guide: Intégration avec Clay

## Qu'est-ce que Clay?

Clay est une plateforme de data enrichment et d'automatisation pour la prospection B2B.

Avec cette intégration, vous pouvez:
- ✅ Enrichir vos contacts Clay avec des emails personnalisés
- ✅ Générer des variables individuelles (persona, competitor, pain point, etc.)
- ✅ Automatiser la génération d'emails à grande échelle
- ✅ Utiliser les agents comme enrichments HTTP

---

## Architecture

```
Clay Table
  ├── Colonnes de base (company_name, website, first_name, etc.)
  ├── HTTP Request enrichment → Votre API
  └── Colonnes enrichies (email_content, target_persona, etc.)
```

---

## Setup Complet

### Étape 1: Déployer l'API

#### Option A: Local (pour tests)

```bash
# 1. Démarrer l'API localement
python -m uvicorn src.api.clay_compatible_api:app --reload --host 0.0.0.0 --port 8000

# 2. Exposer avec ngrok (pour que Clay puisse y accéder)
ngrok http 8000

# Notez l'URL: https://xxxx-xx-xx-xx-xx.ngrok-free.app
```

#### Option B: Production (recommandé)

**Déployer sur Railway.app** (gratuit jusqu'à 500h/mois):

1. Créez un compte sur [railway.app](https://railway.app)

2. Créez un nouveau projet → Deploy from GitHub

3. Liez votre repo GitHub

4. Railway détecte automatiquement FastAPI

5. Configurez les variables d'environnement:
   ```
   OPENAI_API_KEY=sk-proj-...
   API_KEY=votre-cle-secrete
   API_HOST=0.0.0.0
   API_PORT=8000
   ```

6. Notez l'URL de déploiement: `https://votre-projet.railway.app`

**Autres options**:
- [Render.com](https://render.com) (gratuit)
- [Fly.io](https://fly.io) (gratuit 3 VMs)
- Vercel (serverless)
- AWS Lambda / Google Cloud Run

---

### Étape 2: Configurer Clay

#### 2.1 Créer une Table Clay

Colonnes de base:
- `company_name` (texte)
- `first_name` (texte)
- `last_name` (texte)
- `email` (email)
- `company_domain` (URL)
- `industry` (texte)

#### 2.2 Ajouter un HTTP Request Enrichment

1. **Cliquez sur "+ Add Enrichment"**

2. **Sélectionnez "HTTP API"**

3. **Configurez la requête**:

```
Method: POST
URL: https://votre-api.railway.app/api/generate-email

Headers:
  Content-Type: application/json
  X-API-Key: votre-cle-secrete

Body (JSON):
{
  "contact": {
    "company_name": "{{company_name}}",
    "first_name": "{{first_name}}",
    "last_name": "{{last_name}}",
    "email": "{{email}}",
    "website": "{{company_domain}}",
    "industry": "{{industry}}"
  },
  "directives": "Ton professionnel, focus ROI mesurable"
}
```

4. **Mappez les colonnes de sortie**:

Clay va créer automatiquement des colonnes pour:
- `email_content` → Email complet généré
- `target_persona` → Persona identifié
- `competitor_name` → Concurrent principal
- `problem_specific` → Pain point spécifique
- `quality_score` → Score de qualité /100
- etc.

5. **Testez avec 1 ligne**

6. **Lancez sur toutes les lignes**

---

## Workflow Clay Complet

### Méthode 1: Email Complet (Simple)

```
Clay Table
  ├── company_name
  ├── first_name
  ├── company_domain
  └── [HTTP API] → /api/generate-email
      └── email_content (prêt à envoyer!)
```

**Avantages**:
- ✅ 1 seul enrichment
- ✅ Email complet généré
- ✅ Toutes les variables disponibles

**Inconvénients**:
- ⏱️ ~25s par ligne (tous les agents)
- 💰 ~$0.0012 par ligne

---

### Méthode 2: Étapes Séparées (Avancé)

Utilisez les agents individuellement pour plus de contrôle:

```
Clay Table
  ├── company_name
  ├── company_domain
  ├── [HTTP API 1] → /api/extract-persona
  │   ├── target_persona
  │   └── product_category
  ├── [HTTP API 2] → /api/find-competitor
  │   └── competitor_name
  ├── [HTTP API 3] → /api/identify-pain
  │   ├── problem_specific
  │   └── impact_measurable
  └── [Formula] → Assembler l'email custom
```

**Avantages**:
- ✅ Plus de contrôle
- ✅ Peut filtrer entre chaque étape
- ✅ Peut utiliser d'autres enrichments Clay entre les étapes

**Inconvénients**:
- ⚠️ Plus complexe à configurer
- ⏱️ Plusieurs appels API

---

## Exemples de Configuration Clay

### Exemple 1: Email Complet

**HTTP Request**:
```json
POST https://votre-api.railway.app/api/generate-email

Headers:
  X-API-Key: votre-cle

Body:
{
  "contact": {
    "company_name": "{{company_name}}",
    "first_name": "{{first_name}}",
    "website": "{{company_domain}}",
    "industry": "{{industry}}"
  },
  "template": null,
  "directives": "Ton professionnel, focus ROI, éviter jargon",
  "model": "gpt-4o-mini"
}
```

**Output mapping**:
- `response.email_content` → Colonne "Email Final"
- `response.quality_score` → Colonne "Quality Score"
- `response.target_persona` → Colonne "Persona"
- `response.competitor_name` → Colonne "Concurrent"

---

### Exemple 2: Persona Seulement

**HTTP Request**:
```json
POST https://votre-api.railway.app/api/extract-persona

Headers:
  X-API-Key: votre-cle

Body:
{
  "company_name": "{{company_name}}",
  "website": "{{company_domain}}",
  "industry": "{{industry}}"
}
```

**Output mapping**:
- `response.data.target_persona` → Colonne "Persona"
- `response.data.product_category` → Colonne "Product Category"
- `response.confidence_score` → Colonne "Confidence"

---

### Exemple 3: Template Personnalisé

**HTTP Request**:
```json
POST https://votre-api.railway.app/api/generate-email

Body:
{
  "contact": {
    "company_name": "{{company_name}}",
    "first_name": "{{first_name}}",
    "website": "{{company_domain}}"
  },
  "template": "Bonjour {{first_name}},\n\nJ'ai remarqué que {{company_name}} {{specific_signal_1}}.\n\nLe défi: {{problem_specific}}.\nL'impact: {{impact_measurable}}.\n\nRésultat: {{case_study_result}}.\n\nIntéressé(e)?",
  "directives": "Ton très corporate, focus CFO"
}
```

---

## Filtres et Conditions Clay

### Filtrer par Quality Score

Après l'enrichment, ajoutez une formule Clay:

```javascript
// Garder seulement les emails avec quality > 75
if (quality_score > 75) {
  return email_content
} else {
  return "SKIP - Quality trop basse"
}
```

---

### Régénérer si Fallback Élevé

```javascript
// Si le persona a un fallback level > 2, marquer pour review
if (fallback_levels.persona_agent > 2) {
  return "REVIEW REQUIRED"
} else {
  return "OK"
}
```

---

## Intégration avec d'autres Enrichments Clay

### Workflow Optimal

```
1. Clay Find Companies (Apollo/LinkedIn Sales Nav)
   ↓
2. Waterfall enrichment (email, LinkedIn, etc.)
   ↓
3. [VOTRE API] Generate Email
   ↓
4. Filter (quality > 75)
   ↓
5. Send via Instantly/Lemlist/Outreach
```

---

### Combiner avec Scraping Clay

```
1. Clay scrape website (via Apify/Phantombuster)
   ↓
2. [VOTRE API] /api/extract-persona
   (passe le contenu scrapé dans website_content)
   ↓
3. Filter par persona (garder seulement VP Sales)
   ↓
4. [VOTRE API] /api/generate-email
```

---

## Optimisations

### 1. Utiliser le Cache

L'API a un cache intégré. Si vous régénérez pour la même entreprise:
- Cache hit rate: ~83%
- Temps réduit: ~5s au lieu de 25s
- Coût réduit: ~$0.0002 au lieu de $0.0012

### 2. Batch Processing

Au lieu d'appeler 1 ligne à la fois, utilisez l'API Clay Batch:

```python
# TODO: Créer un endpoint /api/batch
POST /api/batch

Body:
{
  "contacts": [
    {"company_name": "Aircall", ...},
    {"company_name": "Stripe", ...},
    {"company_name": "Notion", ...}
  ]
}
```

→ Génère 10 emails en parallèle
→ Coût: même
→ Temps: 30s au lieu de 250s

### 3. Modèle selon Priorité

Dans Clay, utilisez une formule pour choisir le modèle:

```javascript
// VIP clients → gpt-4o (meilleure qualité)
if (company_size > 500 || deal_size > 100000) {
  model = "gpt-4o"
} else {
  // Standard → gpt-4o-mini (économique)
  model = "gpt-4o-mini"
}
```

Passez `model` dans le body de la requête.

---

## Coûts et Limites

### Coûts par Email

| Modèle | Coût API | Temps | Qualité |
|--------|----------|-------|---------|
| gpt-4o-mini | $0.0012 | ~22s | 75/100 |
| gpt-4o | $0.008 | ~25s | 85/100 |

**Pour 1,000 emails**:
- gpt-4o-mini: $1.20
- gpt-4o: $8.00

### Limites Rate

**OpenAI**:
- gpt-4o-mini: 30,000 TPM (tokens per minute)
- ~80 emails/minute possible

**Votre API**:
- Aucune limite si auto-hébergée
- Railway.app: Pas de limite de requêtes

**Clay**:
- HTTP enrichments: Pas de limite native
- Dépend de votre plan Clay

---

## Dépannage

### Erreur 401: Invalid API Key

```
Vérifiez:
1. Header X-API-Key est présent
2. Valeur = celle dans .env (API_KEY)
3. Pas d'espace avant/après
```

### Erreur 500: Template introuvable

```
Solutions:
1. Passez un template custom dans le body
2. Ou uploadez le template par défaut sur le serveur
```

### Timeout (> 30s)

```
Causes:
- Modèle trop lent (gpt-4-turbo)
- Trop de contexte

Solutions:
- Utilisez gpt-4o-mini
- Réduisez le template
- Augmentez le timeout Clay (Settings > 60s)
```

### Quality Score Trop Bas (< 60)

```
Causes:
- Pas assez d'info sur l'entreprise
- Fallback levels élevés
- Directives contradictoires

Solutions:
1. Enrichir avec plus de data Clay avant
2. Améliorer les prompts des agents
3. Utiliser gpt-4o au lieu de gpt-4o-mini
```

---

## Exemples de Use Cases

### Use Case 1: Prospection SDR

**Workflow**:
```
1. Liste LinkedIn Sales Nav (500 contacts)
   ↓
2. Waterfall email (Apollo → Hunter)
   ↓
3. [API] Generate Email (gpt-4o-mini)
   ↓
4. Filter quality > 70
   ↓
5. Send via Instantly
```

**Résultat**:
- 500 contacts
- 450 emails générés (quality > 70)
- Coût: $0.60 (500 × $0.0012)
- Temps: 3h (parallélisé par Clay)

---

### Use Case 2: Account-Based Marketing (ABM)

**Workflow**:
```
1. Liste de 50 comptes target (Fortune 500)
   ↓
2. Scrape website (Apify)
   ↓
3. Find all decision makers (Apollo)
   ↓
4. [API] Generate Email (gpt-4o pour qualité max)
   ↓
5. Review manuel (quality > 80 seulement)
   ↓
6. Send via Outreach
```

**Résultat**:
- 50 comptes × 3 contacts = 150 emails
- Tous quality > 80
- Coût: $1.20 (150 × $0.008)
- Reply rate: +60% vs emails standards

---

### Use Case 3: Event Follow-up

**Workflow**:
```
1. Liste des participants à un salon (CSV upload)
   ↓
2. Enrich (company data)
   ↓
3. [API] Generate Email avec template custom
   (mention du salon dans le template)
   ↓
4. Send immédiatement
```

**Template custom**:
```
Bonjour {{first_name}},

Ravi de vous avoir rencontré au salon {{event_name}}.

Comme discuté, j'ai remarqué que {{company_name}} {{specific_signal_1}}.

Le défi que vous avez mentionné: {{problem_specific}}.

On a aidé {{case_study_result}}.

On se rappelle cette semaine?
```

---

## Monitoring et Analytics

### Dans Clay

Ajoutez des colonnes calculées:

```javascript
// Success rate
countif(quality_score > 75) / count(quality_score)

// Avg quality
average(quality_score)

// Cost tracking
count(email_content) * 0.0012
```

### Dans votre API

Ajoutez un endpoint analytics:

```python
@app.get("/api/analytics")
async def get_analytics():
    return {
        "total_requests": ...,
        "avg_quality_score": ...,
        "total_cost": ...,
        "requests_per_day": ...
    }
```

---

## Sécurité

### 1. API Key Rotation

Changez régulièrement `API_KEY` dans `.env`:

```bash
# Générer une nouvelle clé
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Mettre à jour dans .env
API_KEY=nouvelle-cle-ici

# Mettre à jour dans Clay
```

### 2. Rate Limiting

Ajoutez slowapi pour limiter les abus:

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/generate-email")
@limiter.limit("100/hour")  # Max 100 requêtes/heure par IP
async def generate_email(...):
    ...
```

### 3. Webhooks pour Logs

Envoyez les logs à Clay ou Slack:

```python
# À chaque génération
requests.post(
    "https://hooks.slack.com/...",
    json={
        "text": f"Email généré pour {company_name} - Quality: {quality_score}"
    }
)
```

---

## Prochaines Étapes

1. ✅ **Déployer l'API** → Railway/Render/Vercel
2. ✅ **Tester avec 1 ligne Clay** → Vérifier la connexion
3. ✅ **Ajuster les directives** → Optimiser la qualité
4. ✅ **Tester avec 10 lignes** → Valider la scalabilité
5. ✅ **Lancer en production** → 100+ lignes

---

## Commandes Rapides

```bash
# Démarrer l'API localement
python -m uvicorn src.api.clay_compatible_api:app --reload --port 8000

# Exposer avec ngrok (pour Clay)
ngrok http 8000

# Tester l'endpoint
curl -X POST https://votre-api.com/api/generate-email \
  -H "X-API-Key: votre-cle" \
  -H "Content-Type: application/json" \
  -d '{"contact": {"company_name": "Aircall", "first_name": "Sophie", "website": "https://aircall.io"}}'

# Voir la doc Swagger
# Ouvrez: http://localhost:8000/docs
```

---

## FAQ

**Q: Clay peut-il appeler plusieurs endpoints en séquence?**
R: Oui! Utilisez les enrichments séparés (extract-persona → find-competitor → etc.)

**Q: Puis-je utiliser des données enrichies par d'autres outils Clay?**
R: Oui! Passez-les dans le body JSON via les variables Clay `{{colonnes}}`

**Q: Quel est le timeout maximum?**
R: Par défaut 30s. Augmentez dans les settings Clay si besoin.

**Q: Puis-je voir les logs des requêtes?**
R: Oui, dans les logs Railway/Render, ou ajoutez un webhook Slack

**Q: Le cache fonctionne entre les tables Clay?**
R: Oui, basé sur company_name. Si vous régénérez pour Aircall, c'est caché.

---

Bon setup avec Clay! 🚀
