# 🚀 Guide d'Intégration n8n → Google Sheets

## Vue d'Ensemble

Le système fonctionne avec **3 endpoints API** qui s'enchaînent:

```
1. Coordinator → Génère la stratégie
2. Google Maps → Scrape les entreprises locales
3. JobSpy → Scrape les offres d'emploi (hiring signals)
```

**Résultat**: 3 Google Sheets séparées (1 par source) → Facile à enrichir et segmenter ensuite

---

## Architecture API - Les 3 Endpoints

### 1️⃣ Coordinator Analyze (Le Cerveau)

**Endpoint**: `POST /api/v2/coordinator/analyze`

**Ce qu'il fait**:
- Lit le contexte client depuis Supabase
- Analyse l'ICP, industries, pain points
- Génère automatiquement les recherches optimales

**Request**:
```json
{
  "client_id": "kaleads",
  "target_count": 500,
  "country": "France"
}
```

**Response**:
```json
{
  "success": true,
  "client_name": "Kaleads",
  "pain_type": "lead_generation",
  "strategy": "hybrid",
  
  "google_maps_searches": [
    {
      "query": "agence SaaS",
      "cities": ["Paris", "Lyon", "Marseille"],
      "max_results_per_city": 50
    },
    {
      "query": "startup tech",
      "cities": ["Paris", "Lyon"],
      "max_results_per_city": 30
    }
  ],
  
  "jobspy_searches": [
    {
      "job_title": "Head of Sales",
      "location": "France",
      "company_size": ["11-50", "51-200"],
      "industries": ["SaaS", "Tech"],
      "max_results": 100
    },
    {
      "job_title": "VP Marketing",
      "location": "France",
      "company_size": ["11-50", "51-200"],
      "industries": ["SaaS", "Tech"],
      "max_results": 100
    }
  ],
  
  "estimated_leads": {
    "google_maps": 6250,
    "jobspy": 300,
    "total": 6550
  }
}
```

---

### 2️⃣ Google Maps Search (Entreprises Locales)

**Endpoint**: `POST /api/v2/leads/google-maps`

**Ce qu'il fait**:
- Scrape Google Maps avec RapidAPI
- Cherche le même keyword dans plusieurs villes
- Retourne entreprises avec téléphone, site web, adresse, avis

**Request**:
```json
{
  "query": "agence SaaS",
  "cities": ["Paris", "Lyon", "Marseille"],
  "max_results_per_city": 50
}
```

**Response**:
```json
{
  "success": true,
  "total_leads": 87,
  "cities_searched": ["Paris", "Lyon", "Marseille"],
  "cost_usd": 0.0087,
  
  "leads": [
    {
      "company_name": "Agence XYZ",
      "phone": "+33 1 23 45 67 89",
      "website": "https://agence-xyz.fr",
      "address": "123 rue de Paris, 75001 Paris",
      "city": "Paris",
      "rating": 4.5,
      "reviews_count": 234,
      "place_id": "ChIJ...",
      "search_query": "agence SaaS",
      "source": "google_maps"
    },
    ...
  ]
}
```

---

### 3️⃣ JobSpy Search (Hiring Signals)

**Endpoint**: `POST /api/v2/leads/jobspy`

**Ce qu'il fait**:
- Scrape Indeed, LinkedIn Jobs, etc.
- Trouve les entreprises qui recrutent
- Hiring = Signal d'intention forte (besoin de leads/growth)

**Request**:
```json
{
  "job_title": "Head of Sales",
  "location": "France",
  "company_size": ["11-50", "51-200"],
  "industries": ["SaaS", "Tech"],
  "max_results": 100
}
```

**Response**:
```json
{
  "success": true,
  "total_leads": 78,
  "job_title_searched": "Head of Sales",
  "cost_usd": 0.0,
  
  "leads": [
    {
      "company_name": "Aircall",
      "website": "https://aircall.io",
      "job_title": "Head of Sales France",
      "location": "Paris",
      "company_size": "51-200",
      "posted_date": "2025-11-10",
      "job_url": "https://...",
      "hiring_signal": "Recruiting for Head of Sales = Need leads/pipeline",
      "source": "jobspy",
      "job_board": "LinkedIn Jobs"
    },
    ...
  ]
}
```

---

## 🏗️ Architecture n8n Recommandée

### Workflow Principal: "Lead Generation Master"

```
┌─────────────────────────────────────────────────────────────┐
│                      WORKFLOW N8N                           │
└─────────────────────────────────────────────────────────────┘

[1] Manual Trigger / Cron (1x par semaine par client)
     Input: client_id = "kaleads"
              ↓
[2] HTTP Request → /api/v2/coordinator/analyze
     Output: strategy, google_maps_searches[], jobspy_searches[]
              ↓
              ├─────────────────┬─────────────────┐
              ↓                 ↓                 ↓
              
[3a] GOOGLE MAPS BRANCH     [3b] JOBSPY BRANCH    [3c] LINKEDIN BRANCH (futur)
     ↓                           ↓
     Loop each search            Loop each search
     ↓                           ↓
[4a] HTTP → /leads/google-maps  [4b] HTTP → /leads/jobspy
     ↓                           ↓
[5a] Transform data             [5b] Transform data
     Add columns:                Add columns:
     - client_id                 - client_id
     - campaign_id               - campaign_id
     - date_scraped              - date_scraped
     - source: "google_maps"     - source: "jobspy"
     - enriched: FALSE           - enriched: FALSE
     ↓                           ↓
[6a] Google Sheets              [6b] Google Sheets
     → "Kaleads - Google Maps"  → "Kaleads - JobSpy"
     Append rows                 Append rows
     ↓                           ↓
     └───────────┬───────────────┘
                 ↓
[7] Webhook (optionnel)
    Notifier que la campagne est prête
```

---

## 📊 Structure Google Sheets Recommandée

### Option 1: Une Sheet par Source (RECOMMANDÉ)

**Avantages**:
- Facile à enrichir séparément (Clay, Phantombuster, etc.)
- Colonnes différentes par source
- Pas de confusion
- Meilleure performance

**Sheets à créer**:

#### Sheet 1: "Kaleads - Google Maps"
```
| company_name | phone | website | address | city | rating | reviews_count | search_query | client_id | campaign_id | date_scraped | enriched | email | linkedin_url |
```

#### Sheet 2: "Kaleads - JobSpy"
```
| company_name | website | job_title | location | company_size | posted_date | job_url | hiring_signal | client_id | campaign_id | date_scraped | enriched | email | linkedin_company |
```

#### Sheet 3: "Kaleads - Master List" (optionnel)
```
| company_name | website | source | city | industry_detected | icp_score | enriched | email | linkedin_url | status | assigned_to |
```

### Option 2: Une Sheet Unifiée avec Colonne "Source"

**Avantages**:
- Vue centralisée
- Dédupliquation automatique plus facile

**Inconvénients**:
- Beaucoup de colonnes vides (selon la source)
- Moins flexible pour enrichissement

```
| company_name | website | source | phone | address | city | job_title | hiring_signal | rating | enriched | email | ...
| Aircall | ... | jobspy | NULL | NULL | Paris | Head of Sales | recruiting | NULL | FALSE | ... |
| Agence XYZ | ... | google_maps | +33... | 123 rue... | Paris | NULL | NULL | 4.5 | FALSE | ... |
```

---

## 🔄 Workflow n8n Détaillé - Pas à Pas

### Node 1: Manual Trigger / Cron

```
Trigger Type: Schedule
Cron: 0 9 * * 1  (Tous les lundis à 9h)

Ou Manual avec formulaire:
- Input: client_id (dropdown: kaleads, client2, client3)
- Input: target_count (default: 500)
```

### Node 2: Coordinator Analyze

```
Node Type: HTTP Request
Method: POST
URL: http://your-api:8001/api/v2/coordinator/analyze
Headers:
  Content-Type: application/json
  X-API-Key: {{ $env.KALEADS_API_KEY }}
Body (JSON):
  {
    "client_id": "{{ $json.client_id }}",
    "target_count": 500,
    "country": "France"
  }
```

**Output sera disponible dans `$json.google_maps_searches` et `$json.jobspy_searches`**

### Node 3a: Loop Google Maps Searches

```
Node Type: Split In Batches
Batch Size: 1
Input: {{ $json.google_maps_searches }}
```

### Node 4a: Execute Google Maps Search

```
Node Type: HTTP Request
Method: POST
URL: http://your-api:8001/api/v2/leads/google-maps
Headers:
  Content-Type: application/json
  X-API-Key: {{ $env.KALEADS_API_KEY }}
Body (JSON):
  {
    "query": "{{ $json.query }}",
    "cities": {{ $json.cities }},
    "max_results_per_city": {{ $json.max_results_per_city }}
  }
```

### Node 5a: Transform Google Maps Data

```
Node Type: Function / Code
Code (JavaScript):

// Ajouter des colonnes pour tracking
const leads = $input.item.json.leads;
const client_id = $("Node 1").item.json.client_id;
const campaign_id = `${client_id}_${new Date().toISOString().split('T')[0]}`;

return leads.map(lead => ({
  ...lead,
  client_id: client_id,
  campaign_id: campaign_id,
  date_scraped: new Date().toISOString(),
  enriched: false,
  email: '',
  linkedin_url: ''
}));
```

### Node 6a: Append to Google Sheets

```
Node Type: Google Sheets
Operation: Append
Spreadsheet: Kaleads - Google Maps
Sheet: Sheet1
Columns: Auto-map from input

Settings:
- ✅ Skip empty values
- ✅ Use first row as headers
```

### Node 3b-6b: Répéter pour JobSpy

(Même logique mais avec `/api/v2/leads/jobspy` et sheet "Kaleads - JobSpy")

---

## 🎯 Workflow d'Enrichissement (Séparé)

Une fois les leads dans Google Sheets, créer un 2ème workflow:

```
[1] Google Sheets Trigger
    Watch for new rows (enriched = FALSE)
         ↓
[2] Split In Batches (10 leads à la fois)
         ↓
[3] Enrichissement (Clay / Phantombuster / Apollo)
    - Trouver email
    - Trouver LinkedIn
    - Vérifier site web valide
         ↓
[4] Update Google Sheets
    Set enriched = TRUE
    Fill email, linkedin_url
         ↓
[5] Filter: ICP Match?
    Check if fits target_industries, company_size
         ↓
[6a] If YES → Move to "Master List"
[6b] If NO → Mark as "not_target"
```

---

## 📋 Template n8n à Importer

### Workflow JSON Structure

```json
{
  "name": "Kaleads - Lead Generation Master",
  "nodes": [
    {
      "name": "Manual Trigger",
      "type": "n8n-nodes-base.manualTrigger",
      "position": [250, 300]
    },
    {
      "name": "Coordinator Analyze",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300],
      "parameters": {
        "url": "http://your-api:8001/api/v2/coordinator/analyze",
        "method": "POST",
        "authentication": "headerAuth",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {"name": "client_id", "value": "kaleads"},
            {"name": "target_count", "value": 500}
          ]
        }
      }
    },
    {
      "name": "Loop Google Maps",
      "type": "n8n-nodes-base.splitInBatches",
      "position": [650, 200],
      "parameters": {
        "batchSize": 1,
        "options": {
          "reset": false
        }
      }
    },
    {
      "name": "Execute Google Maps Search",
      "type": "n8n-nodes-base.httpRequest",
      "position": [850, 200],
      "parameters": {
        "url": "http://your-api:8001/api/v2/leads/google-maps",
        "method": "POST",
        "sendBody": true
      }
    },
    {
      "name": "Transform Google Maps Data",
      "type": "n8n-nodes-base.function",
      "position": [1050, 200]
    },
    {
      "name": "Append to Google Sheets (GMaps)",
      "type": "n8n-nodes-base.googleSheets",
      "position": [1250, 200],
      "parameters": {
        "operation": "append",
        "sheetId": "your-sheet-id",
        "range": "Sheet1"
      }
    },
    {
      "name": "Loop JobSpy",
      "type": "n8n-nodes-base.splitInBatches",
      "position": [650, 400]
    },
    {
      "name": "Execute JobSpy Search",
      "type": "n8n-nodes-base.httpRequest",
      "position": [850, 400]
    },
    {
      "name": "Transform JobSpy Data",
      "type": "n8n-nodes-base.function",
      "position": [1050, 400]
    },
    {
      "name": "Append to Google Sheets (JobSpy)",
      "type": "n8n-nodes-base.googleSheets",
      "position": [1250, 400]
    }
  ],
  "connections": {
    "Manual Trigger": {"main": [[{"node": "Coordinator Analyze"}]]},
    "Coordinator Analyze": {"main": [[{"node": "Loop Google Maps"}, {"node": "Loop JobSpy"}]]},
    "Loop Google Maps": {"main": [[{"node": "Execute Google Maps Search"}]]},
    "Execute Google Maps Search": {"main": [[{"node": "Transform Google Maps Data"}]]},
    "Transform Google Maps Data": {"main": [[{"node": "Append to Google Sheets (GMaps)"}]]},
    "Append to Google Sheets (GMaps)": {"main": [[{"node": "Loop Google Maps"}]]}
  }
}
```

---

## 🔐 Configuration Requise

### Variables d'Environnement n8n

```bash
# Dans n8n Settings → Environment Variables
KALEADS_API_URL=http://your-server:8001
KALEADS_API_KEY=lL^nc2U%tU8f2!LH48!29!mW8
```

### Credentials n8n

1. **HTTP Header Auth** (pour API Kaleads)
   - Name: X-API-Key
   - Value: {{ $env.KALEADS_API_KEY }}

2. **Google Sheets OAuth2**
   - Suivre le wizard n8n
   - Permissions: Read & Write

---

## 🚀 Utilisation par Client

### Pour ajouter un nouveau client:

1. **Ajouter le client dans Supabase** (table `client_contexts`)
   - Remplir: client_id, client_name, company_profile, personas, etc.

2. **Dupliquer le workflow n8n**
   - Renommer: "Client2 - Lead Generation Master"
   - Changer: `client_id` dans le trigger

3. **Créer les Google Sheets**
   - "Client2 - Google Maps"
   - "Client2 - JobSpy"

4. **Lancer**
   - Le coordinateur analysera automatiquement le contexte
   - Génèrera des recherches adaptées à l'ICP du client
   - Remplira les sheets spécifiques au client

---

## 📊 Exemple Complet - Cas Kaleads

### Input
```
client_id: kaleads
target_count: 500
```

### Coordinator Output
```
Strategy: hybrid
Google Maps: 5 recherches × 25 villes = 6,250 leads
JobSpy: 3 recherches = 300 leads
Total: 6,550 leads
```

### Résultat dans Google Sheets

**Sheet "Kaleads - Google Maps"**: 6,250 lignes
```
agence SaaS, startup tech, éditeur de logiciel...
Paris, Lyon, Marseille, Toulouse...
```

**Sheet "Kaleads - JobSpy"**: 300 lignes
```
Head of Sales, VP Marketing, Business Developer...
Entreprises qui recrutent = Signal fort
```

### Enrichissement
```
Clay workflow:
1. Lire Google Sheet
2. Enrichir email (Hunter.io)
3. Enrichir LinkedIn (Phantombuster)
4. Vérifier ICP match
5. Transférer vers Master List si qualifié
```

### Campagne Email
```
Clay → Generate email with Kaleads email template
→ Send via Lemlist/Instantly
→ Track replies in CRM
```

---

## 💡 Best Practices

### 1. Séparation par Source
- ✅ Gardez Google Maps et JobSpy séparés initialement
- ✅ Fusionnez après enrichissement dans une Master List
- ✅ Déduplication sur company_name + website

### 2. Tracking
- ✅ Toujours ajouter: client_id, campaign_id, date_scraped
- ✅ Colonne `enriched` pour savoir ce qui est prêt
- ✅ Colonne `status` pour le suivi (new, contacted, replied, qualified)

### 3. Performance
- ✅ Batch processing (10-50 leads à la fois)
- ✅ Rate limiting sur les enrichments
- ✅ Cron scheduling (1x par semaine, pas tous les jours)

### 4. Résilience
- ✅ Error handling sur chaque node HTTP
- ✅ Retry logic (3 tentatives avec backoff)
- ✅ Webhook de notification en cas d'échec
- ✅ Logs détaillés (n8n execution history)

---

## 🎯 Résumé - Quick Start

1. **Setup API**: Lancer l'API avec les bons ENV vars
2. **Créer Google Sheets**: 2 sheets par client (Google Maps + JobSpy)
3. **Importer Workflow n8n**: Copier le template ci-dessus
4. **Configurer Credentials**: API Key + Google Sheets OAuth
5. **Tester**: Lancer manuellement pour "kaleads"
6. **Automatiser**: Activer le cron (1x par semaine)
7. **Enrichir**: Setup Clay workflow pour enrichissement
8. **Campagne**: Utiliser les leads enrichis pour emailing

**Temps de setup**: ~2 heures
**Résultat**: 500-6000 leads qualifiés par client par semaine automatiquement 🚀

