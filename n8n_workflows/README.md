# 🚀 Workflows n8n - Lead Generation

Ce dossier contient les workflows n8n prêts à importer pour automatiser la génération de leads.

---

## 📁 Fichiers

- **`lead_generation_master.json`** - Workflow principal qui orchestre tout
- **`GUIDE_INTEGRATION_N8N_SHEETS.md`** - Guide complet d'intégration (dans le dossier parent)

---

## ⚡ Quick Start (5 minutes)

### 1. Préparer Google Sheets

Créer 2 nouvelles Google Sheets:

**Sheet 1: "Kaleads - Google Maps"**
Colonnes (première ligne):
```
company_name | phone | website | address | city | rating | reviews_count | place_id | search_query | client_id | campaign_id | date_scraped | source | enriched | email | linkedin_url | linkedin_company | industry | status
```

**Sheet 2: "Kaleads - JobSpy"**
Colonnes (première ligne):
```
company_name | website | job_title | location | company_size | posted_date | job_url | hiring_signal | job_board | client_id | campaign_id | date_scraped | source | enriched | email | phone | linkedin_url | linkedin_company | industry | status
```

Copier les IDs des sheets (dans l'URL: `https://docs.google.com/spreadsheets/d/[ID_ICI]/edit`)

---

### 2. Configurer n8n

#### A. Credentials

**1. Créer credential "Kaleads API Key"**:
- Type: `Header Auth`
- Name: `X-API-Key`
- Value: `lL^nc2U%tU8f2!LH48!29!mW8`

**2. Créer credential "Google Sheets OAuth"**:
- Type: `Google Sheets OAuth2`
- Suivre le wizard n8n pour autoriser l'accès

#### B. Importer le Workflow

1. Dans n8n: Aller dans **Workflows**
2. Cliquer **Import from File**
3. Sélectionner `lead_generation_master.json`
4. Le workflow s'ouvre automatiquement

#### C. Configurer les Nodes

**Dans "Set Parameters"**:
```json
{
  "client_id": "kaleads",  // ← Changer selon le client
  "target_count": "500",
  "country": "France"
}
```

**Dans "Coordinator Analyze"**:
- URL: `http://localhost:8001/api/v2/coordinator/analyze`
  (Remplacer `localhost:8001` par l'adresse de ton API)
- Credentials: Sélectionner "Kaleads API Key"

**Dans "Execute Google Maps Search"**:
- URL: `http://localhost:8001/api/v2/leads/google-maps`
- Credentials: Sélectionner "Kaleads API Key"

**Dans "Execute JobSpy Search"**:
- URL: `http://localhost:8001/api/v2/leads/jobspy`
- Credentials: Sélectionner "Kaleads API Key"

**Dans "Append to Google Sheets (GMaps)"**:
- Document ID: Coller l'ID de ta sheet "Kaleads - Google Maps"
- Sheet Name: `Sheet1`
- Credentials: Sélectionner "Google Sheets OAuth"

**Dans "Append to Google Sheets (JobSpy)"**:
- Document ID: Coller l'ID de ta sheet "Kaleads - JobSpy"
- Sheet Name: `Sheet1`
- Credentials: Sélectionner "Google Sheets OAuth"

---

### 3. Tester

1. S'assurer que l'API est lancée:
```bash
cd kaleads-atomic-agents
python -m uvicorn src.api.n8n_optimized_api:app --host 0.0.0.0 --port 8001
```

2. Dans n8n: Cliquer **Execute Workflow**

3. Observer:
   - Le coordinator analyse le contexte Kaleads
   - Les recherches Google Maps se lancent en boucle
   - Les recherches JobSpy se lancent en parallèle
   - Les Google Sheets se remplissent automatiquement

4. Vérifier les Google Sheets:
   - Sheet "Google Maps": ~6,250 lignes avec entreprises
   - Sheet "JobSpy": ~300 lignes avec hiring signals

---

## 🔄 Automatisation (Cron)

Pour lancer automatiquement chaque semaine:

1. **Remplacer "Manual Trigger"** par **"Schedule Trigger"**
   - Type: `Schedule Trigger`
   - Cron Expression: `0 9 * * 1` (Tous les lundis à 9h)
   - Timezone: `Europe/Paris`

2. **Activer le workflow**
   - Toggle "Active" en haut à droite

---

## 📊 Flow des Données

```
┌─────────────────┐
│ Manual Trigger  │
│  client_id:     │
│  "kaleads"      │
└────────┬────────┘
         ↓
┌─────────────────────────────┐
│ Coordinator Analyze         │
│ ✓ Lit contexte Supabase     │
│ ✓ Détecte ICP, pain, etc.   │
│ ✓ Génère recherches optimales│
└──────────┬──────────────────┘
           ↓
    ┌──────┴──────┐
    ↓             ↓
┌──────────┐  ┌──────────┐
│ Google   │  │ JobSpy   │
│ Maps     │  │ Searches │
│ Searches │  │          │
└────┬─────┘  └────┬─────┘
     ↓             ↓
   Loop          Loop
     ↓             ↓
  Execute       Execute
   API           API
     ↓             ↓
 Transform     Transform
   Data          Data
     ↓             ↓
┌──────────┐  ┌──────────┐
│ Google   │  │ Google   │
│ Sheet    │  │ Sheet    │
│ (GMaps)  │  │ (JobSpy) │
└──────────┘  └──────────┘
```

---

## 🎯 Adaptation par Client

Pour ajouter un nouveau client (ex: "client2"):

### Option 1: Dupliquer le Workflow (Recommandé)

1. **Dupliquer** le workflow:
   - Menu → Duplicate
   - Renommer: "Client2 - Lead Generation Master"

2. **Modifier "Set Parameters"**:
   ```json
   {
     "client_id": "client2",
     "target_count": "1000",
     "country": "France"
   }
   ```

3. **Créer nouvelles Google Sheets**:
   - "Client2 - Google Maps"
   - "Client2 - JobSpy"

4. **Mettre à jour les IDs** dans les nodes "Append to Google Sheets"

5. **Lancer** → Le coordinator s'adaptera automatiquement à l'ICP du client2

### Option 2: Workflow Unique Multi-Clients

Modifier "Set Parameters" pour accepter un input dynamique:
```json
{
  "client_id": "={{ $json.client_id }}",
  "target_count": "500"
}
```

Puis utiliser un node "Switch" au début pour router vers différentes Google Sheets selon le client.

---

## 🔧 Troubleshooting

### Erreur: "Connection refused"
- ✅ Vérifier que l'API est bien lancée sur le port 8001
- ✅ Vérifier l'URL dans les nodes HTTP Request

### Erreur: "Invalid API Key"
- ✅ Vérifier le credential "Kaleads API Key"
- ✅ S'assurer que la clé est correcte: `lL^nc2U%tU8f2!LH48!29!mW8`

### Erreur: "Client not found"
- ✅ Vérifier que le client_id existe dans Supabase (table `client_contexts`)
- ✅ Vérifier que `SUPABASE_SERVICE_ROLE_KEY` est configurée dans l'API

### Google Sheets: "Permission denied"
- ✅ Re-autoriser Google Sheets OAuth dans n8n
- ✅ Vérifier que le Google Sheet est bien partagé avec le compte OAuth

### Pas de données dans les Sheets
- ✅ Vérifier les logs d'exécution n8n (onglet Executions)
- ✅ Tester chaque node individuellement (bouton "Execute Node")
- ✅ Vérifier que les scrapers (Google Maps API, JobSpy) sont bien configurés

---

## 📈 Monitoring

### Vérifier l'exécution

1. **n8n Executions**:
   - Aller dans "Executions" (menu gauche)
   - Voir l'historique de chaque run
   - Inspecter les erreurs éventuelles

2. **Google Sheets**:
   - Compter le nombre de lignes ajoutées
   - Vérifier la colonne `date_scraped` pour voir la dernière exécution

3. **API Logs**:
   - Consulter les logs de l'API pour voir les requêtes
   - Vérifier les temps de réponse

---

## 🚀 Next Steps

Après avoir des leads dans Google Sheets:

1. **Enrichissement** (via Clay/Phantombuster):
   - Ajouter emails
   - Ajouter LinkedIn
   - Vérifier ICP match

2. **Scoring**:
   - Calculer un ICP score (0-100)
   - Prioriser les meilleurs leads

3. **Campagne Email**:
   - Utiliser les templates Kaleads
   - Lancer via Lemlist/Instantly
   - Tracker les réponses

4. **CRM Sync**:
   - Envoyer vers HubSpot/Pipedrive
   - Assigner aux commerciaux

---

## 💡 Best Practices

- ✅ Lancer 1x par semaine maximum (éviter le spam)
- ✅ Garder les sources séparées initialement
- ✅ Enrichir avant de fusionner
- ✅ Dédupliquer sur company_name + website
- ✅ Monitorer les coûts (RapidAPI Google Maps)
- ✅ Backuper les Google Sheets régulièrement

---

## 📞 Support

Questions? Consulter:
- `GUIDE_INTEGRATION_N8N_SHEETS.md` (guide complet)
- `PLAN_AGENT_COORDINATEUR_LEAD_GEN.md` (plan technique)
- Logs API: Check terminal où l'API tourne
- Logs n8n: Onglet "Executions"

