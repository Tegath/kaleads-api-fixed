# ⚡ Quick Start - n8n Integration

Guide ultra-rapide pour lancer la génération de leads automatique.

---

## 🎯 Ce que ça fait

**INPUT**: Tu cliques sur un bouton dans n8n avec un `client_id`

**OUTPUT**: 30 minutes plus tard, tu as 500-6000 leads qualifiés dans Google Sheets, segmentés par source, prêts à enrichir

**MAGIE**: Le système analyse automatiquement le contexte client (ICP, industries, pain points) et génère les recherches optimales sans que tu aies à réfléchir aux mots-clés

---

## 🚀 Setup en 10 Minutes

### 1. Lancer l'API (Terminal 1)

```bash
cd kaleads-atomic-agents

# Activer venv
.\venv\Scripts\Activate.ps1

# Définir les variables d'environnement
$env:SUPABASE_URL="https://ckrspaktqohjenqfuuzl.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNrcnNwYWt0cW9oamVucWZ1dXpsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjYxNjQyMiwiZXhwIjoyMDc4MTkyNDIyfQ.uxZKZuCqZJnadg7ysnliZ5M4TfcKIl5jbW-eR1mpiBU"

# Lancer API
python -m uvicorn src.api.n8n_optimized_api:app --host 0.0.0.0 --port 8001

# ✅ L'API tourne maintenant sur http://localhost:8001
```

### 2. Créer les Google Sheets

**Créer 2 nouvelles Google Sheets**:

1. **"Kaleads - Google Maps"**
   - Copier la première ligne de `n8n_workflows/GOOGLE_SHEETS_TEMPLATES.md` (Template 1)

2. **"Kaleads - JobSpy"**
   - Copier la première ligne de `n8n_workflows/GOOGLE_SHEETS_TEMPLATES.md` (Template 2)

**Copier les IDs** (dans l'URL après `/d/`)

### 3. Importer dans n8n

1. Ouvrir n8n
2. **Import from File** → Sélectionner `n8n_workflows/lead_generation_master.json`
3. Le workflow s'ouvre

### 4. Configurer n8n

**A. Credentials**:
- **Kaleads API Key**: Type `Header Auth`, Name `X-API-Key`, Value `lL^nc2U%tU8f2!LH48!29!mW8`
- **Google Sheets OAuth**: Suivre le wizard

**B. Dans chaque node HTTP Request**:
- Remplacer `localhost:8001` par l'adresse de ton API si elle tourne ailleurs

**C. Dans les 2 nodes "Append to Google Sheets"**:
- Coller les Sheet IDs copiés à l'étape 2

### 5. Tester

Cliquer **Execute Workflow** dans n8n

**Résultat attendu (30 min)**:
- ✅ Google Maps: ~6,250 leads (entreprises SaaS/Tech en France)
- ✅ JobSpy: ~300 leads (entreprises qui recrutent Sales/Marketing)

---

## 🔄 Comment ça Fonctionne

### Flow des Données

```
┌─────────────────────────────────────────────────────────┐
│ 1. COORDINATOR ANALYZE                                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  POST /api/v2/coordinator/analyze                       │
│  Input: { client_id: "kaleads" }                        │
│                                                          │
│  ✓ Lit contexte Supabase (ICP, industries, personas)   │
│  ✓ Détecte pain_type: "lead_generation"                │
│  ✓ Stratégie: "hybrid" (Google Maps + JobSpy)          │
│  ✓ Génère 5 recherches Google Maps optimisées          │
│  ✓ Génère 3 recherches JobSpy optimisées               │
│                                                          │
│  Output: {                                               │
│    google_maps_searches: [                              │
│      { query: "agence SaaS", cities: [25 villes] },    │
│      { query: "startup tech", cities: [25 villes] },   │
│      ...                                                 │
│    ],                                                    │
│    jobspy_searches: [                                    │
│      { job_title: "Head of Sales", location: "France" },│
│      { job_title: "VP Marketing", location: "France" }, │
│      ...                                                 │
│    ]                                                     │
│  }                                                       │
└─────────────────────────────────────────────────────────┘
                         ↓
        ┌────────────────┴────────────────┐
        ↓                                  ↓
┌──────────────────────┐         ┌──────────────────────┐
│ 2a. GOOGLE MAPS      │         │ 2b. JOBSPY           │
├──────────────────────┤         ├──────────────────────┤
│                      │         │                      │
│ Loop chaque query    │         │ Loop chaque query    │
│                      │         │                      │
│ POST /leads/         │         │ POST /leads/jobspy   │
│   google-maps        │         │                      │
│                      │         │ Input: {             │
│ Input: {             │         │   job_title: "Head   │
│   query: "agence     │         │     of Sales",       │
│     SaaS",           │         │   location: "France" │
│   cities: ["Paris",  │         │ }                    │
│     "Lyon", ...],    │         │                      │
│   max_per_city: 50   │         │ ✓ Scrape Indeed,     │
│ }                    │         │   LinkedIn Jobs      │
│                      │         │ ✓ Trouve entreprises │
│ ✓ Scrape Google Maps │         │   qui recrutent      │
│ ✓ Extract: name,     │         │                      │
│   phone, website,    │         │ Output: 78 leads     │
│   address, rating    │         │ (entreprises)        │
│                      │         │                      │
│ Output: 87 leads     │         └──────────┬───────────┘
│ (entreprises)        │                    ↓
└──────────┬───────────┘         ┌──────────────────────┐
           ↓                     │ 3b. TRANSFORM        │
┌──────────────────────┐         │                      │
│ 3a. TRANSFORM        │         │ Add columns:         │
│                      │         │ - client_id          │
│ Add columns:         │         │ - campaign_id        │
│ - client_id          │         │ - date_scraped       │
│ - campaign_id        │         │ - source: "jobspy"   │
│ - date_scraped       │         │ - enriched: FALSE    │
│ - source:            │         │                      │
│   "google_maps"      │         └──────────┬───────────┘
│ - enriched: FALSE    │                    ↓
│                      │         ┌──────────────────────┐
└──────────┬───────────┘         │ 4b. GOOGLE SHEETS    │
           ↓                     │                      │
┌──────────────────────┐         │ Append to:           │
│ 4a. GOOGLE SHEETS    │         │ "Kaleads - JobSpy"   │
│                      │         │                      │
│ Append to:           │         │ Result: 300 rows     │
│ "Kaleads - Google    │         └──────────────────────┘
│  Maps"               │
│                      │
│ Result: 6,250 rows   │
└──────────────────────┘
```

### Les 3 Endpoints API

**1. Coordinator** (Le cerveau)
```bash
POST http://localhost:8001/api/v2/coordinator/analyze
Body: { "client_id": "kaleads", "target_count": 500 }

→ Génère la stratégie optimale
```

**2. Google Maps** (Entreprises locales)
```bash
POST http://localhost:8001/api/v2/leads/google-maps
Body: { "query": "agence SaaS", "cities": ["Paris", "Lyon"] }

→ Scrape Google Maps via RapidAPI
```

**3. JobSpy** (Hiring signals)
```bash
POST http://localhost:8001/api/v2/leads/jobspy
Body: { "job_title": "Head of Sales", "location": "France" }

→ Scrape offres d'emploi (Indeed, LinkedIn Jobs)
```

---

## 📊 Structure des Google Sheets

### Sheet 1: "Kaleads - Google Maps"

**Colonnes clés**:
- `company_name`, `phone`, `website`, `address`, `city`
- `rating` (note Google), `reviews_count`
- `client_id`, `campaign_id`, `date_scraped`
- `enriched` (FALSE par défaut)
- `email`, `linkedin_url` (vides, à enrichir après)

**Exemple**:
```
Agence XYZ | +33123456789 | xyz.fr | Paris | 4.5 | 234 | kaleads | kaleads_2025-11-17 | google_maps | FALSE | | |
```

### Sheet 2: "Kaleads - JobSpy"

**Colonnes clés**:
- `company_name`, `website`, `job_title`, `location`
- `company_size` (ex: 51-200), `posted_date`
- `hiring_signal` (ex: "Recruiting for Sales = Need leads")
- `client_id`, `campaign_id`, `date_scraped`
- `enriched` (FALSE par défaut)
- `email`, `linkedin_url` (vides, à enrichir après)

**Exemple**:
```
Aircall | aircall.io | Head of Sales | Paris | 51-200 | 2025-11-10 | Recruiting for Sales = Need leads | kaleads | kaleads_2025-11-17 | jobspy | FALSE | | |
```

---

## 🔄 Workflow Enrichissement (Étape Suivante)

Une fois les leads dans Google Sheets:

```
┌─────────────────────────────────┐
│ 1. Google Sheets Trigger        │
│    Watch for: enriched = FALSE  │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│ 2. Clay / Phantombuster         │
│    ✓ Find email (Hunter.io)     │
│    ✓ Find LinkedIn              │
│    ✓ Verify website active      │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│ 3. Update Google Sheets         │
│    Set enriched = TRUE          │
│    Fill email, linkedin_url     │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│ 4. ICP Scoring                  │
│    Score 0-100 based on:        │
│    - Industry match             │
│    - Company size match         │
│    - Location match             │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│ 5. If ICP Score > 70            │
│    → Move to "Master List"      │
│    → Ready for email campaign   │
└─────────────────────────────────┘
```

---

## 🎯 Adaptation Multi-Clients

### Pour ajouter "Client2":

**Option 1: Workflow Séparé (SIMPLE)**

1. **Dupliquer** le workflow n8n
2. Renommer: "Client2 - Lead Generation"
3. Modifier "Set Parameters": `client_id: "client2"`
4. Créer 2 nouvelles Google Sheets pour Client2
5. Mettre à jour les Sheet IDs
6. **DONE** → Le coordinator s'adaptera automatiquement à l'ICP de Client2

**Option 2: Workflow Unique Multi-Clients (AVANCÉ)**

1. Ajouter un node "Switch" au début qui route selon `client_id`
2. Chaque branche pointe vers ses propres Google Sheets
3. Plus complexe mais plus maintenable à grande échelle

---

## 💡 Best Practices

### Fréquence

- ✅ **1x par semaine maximum** par client
- ✅ Lundi matin (pour avoir les leads enrichis en milieu de semaine)
- ❌ Ne pas lancer tous les jours (spam + coûts inutiles)

### Organisation

- ✅ **Séparer les sources** (Google Maps ≠ JobSpy) initialement
- ✅ **Fusionner après enrichissement** dans une Master List
- ✅ **Dédupliquer** sur `company_name` + `website`

### Monitoring

- ✅ Vérifier les **Executions** n8n (historique des runs)
- ✅ Compter les lignes dans Google Sheets
- ✅ Vérifier la colonne `date_scraped` (dernière exécution)

### Coûts

- Google Maps: ~$0.01 par 100 leads (RapidAPI)
- JobSpy: Gratuit (scraping direct)
- n8n: Gratuit si self-hosted
- **Total**: ~$0.60 pour 6000 leads 🎉

---

## 🔧 Troubleshooting

### Erreur: "Connection refused"
```bash
# Vérifier que l'API tourne
curl http://localhost:8001/health

# Si erreur, relancer l'API
python -m uvicorn src.api.n8n_optimized_api:app --host 0.0.0.0 --port 8001
```

### Erreur: "Client not found"
```bash
# Vérifier que "kaleads" existe dans Supabase
# Table: client_contexts
# Colonne: client_id = "kaleads"
```

### Pas de données dans Google Sheets
1. ✅ Vérifier les logs n8n (onglet Executions)
2. ✅ Tester chaque node individuellement (bouton "Execute Node")
3. ✅ Vérifier que Google Sheets est bien partagé avec le compte OAuth

### Données incomplètes
1. ✅ Vérifier que les headers des Google Sheets matchent exactement
2. ✅ Utiliser "Auto-map" dans les nodes Google Sheets
3. ✅ Vérifier le code dans "Transform Data" nodes

---

## 📈 Résultats Attendus

### Pour Kaleads (Lead Gen B2B)

**Input**: `client_id: "kaleads"`

**Coordinator Output**:
- Pain Type: `lead_generation`
- Strategy: `hybrid`
- Google Maps: 5 queries × 25 cities = 6,250 leads
- JobSpy: 3 queries = 300 leads
- **Total: 6,550 leads**

**Google Sheets après 30 min**:
- ✅ "Kaleads - Google Maps": 6,250 entreprises SaaS/Tech
- ✅ "Kaleads - JobSpy": 300 entreprises qui recrutent (signal fort)

**Après enrichissement** (Clay/Phantombuster):
- ✅ ~4,500 emails trouvés (70% success rate)
- ✅ ~5,000 LinkedIn trouvés (75% success rate)

**Après ICP scoring**:
- ✅ ~2,000 leads qualifiés (ICP score > 70)
- ✅ Prêts pour campagne email

**ROI**:
- Coût: $0.60 (scraping)
- Temps: 30 min automatique
- Résultat: 2,000 leads qualifiés
- **→ $0.0003 par lead qualifié** 🚀

---

## 🎓 Next Steps

1. **Setup complet** (10 min) → Suivre les étapes ci-dessus
2. **Premier run** (30 min) → Lancer manuellement dans n8n
3. **Vérifier résultats** → Check Google Sheets
4. **Setup enrichissement** → Clay/Phantombuster workflow
5. **ICP scoring** → Filtrer les meilleurs leads
6. **Campagne email** → Utiliser templates Kaleads
7. **Automatiser** → Activer cron (1x par semaine)

---

## 📚 Ressources

- **Guide Complet**: `GUIDE_INTEGRATION_N8N_SHEETS.md`
- **Workflow n8n**: `n8n_workflows/lead_generation_master.json`
- **Templates Sheets**: `n8n_workflows/GOOGLE_SHEETS_TEMPLATES.md`
- **Setup Workflow**: `n8n_workflows/README.md`
- **Plan Technique**: `PLAN_AGENT_COORDINATEUR_LEAD_GEN.md`

---

**Questions?** Check les logs:
- API: Terminal où tourne uvicorn
- n8n: Onglet "Executions"
- Supabase: Dashboard → Table Editor

