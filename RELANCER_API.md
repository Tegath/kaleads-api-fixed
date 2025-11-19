# 🚀 Relancer l'API - Commandes Rapides

Guide pour relancer l'API en local et tester.

---

## ⚡ Commandes PowerShell (Windows)

### 1. Ouvrir PowerShell dans le dossier

```powershell
cd "H:\Mon Drive\TLDRAW\YNAB_app\development_project\Projet_Work\kaleads-atomic-agents"
```

### 2. Activer le venv

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Définir les variables d'environnement

```powershell
$env:SUPABASE_URL="https://ckrspaktqohjenqfuuzl.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNrcnNwYWt0cW9oamVucWZ1dXpsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjYxNjQyMiwiZXhwIjoyMDc4MTkyNDIyfQ.uxZKZuCqZJnadg7ysnliZ5M4TfcKIl5jbW-eR1mpiBU"
```

### 4. Lancer l'API

```powershell
python -m uvicorn src.api.n8n_optimized_api:app --host 0.0.0.0 --port 8001 --reload
```

**✅ L'API tourne maintenant sur: `http://localhost:8001`**

---

## 🧪 Tester que l'API Fonctionne

### Test 1: Health Check (dans un nouveau terminal)

```powershell
curl http://localhost:8001/health
```

**Résultat attendu**:
```json
{
  "status": "healthy",
  "openrouter_key_configured": true,
  "supabase_configured": true,
  "version": "3.0.0"
}
```

### Test 2: Coordinator Analyze (le plus important)

```powershell
curl -X POST http://localhost:8001/api/v2/coordinator/analyze `
  -H "Content-Type: application/json" `
  -H "X-API-Key: lL^nc2U%tU8f2!LH48!29!mW8" `
  -d '{\"client_id\": \"kaleads\", \"target_count\": 500, \"country\": \"France\"}' `
  | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Résultat attendu**:
```json
{
  "success": true,
  "client_name": "Kaleads",
  "pain_type": "lead_generation",
  "strategy": "hybrid",
  "google_maps_searches": [ ... ],
  "jobspy_searches": [ ... ],
  "estimated_leads": {
    "google_maps": 6250,
    "jobspy": 300,
    "total": 6550
  }
}
```

---

## 🎯 Script Tout-en-Un (Copier-Coller)

Créer un fichier `start_api.ps1`:

```powershell
# start_api.ps1
Write-Host "🚀 Démarrage API Kaleads..." -ForegroundColor Green

# Navigate to project
cd "H:\Mon Drive\TLDRAW\YNAB_app\development_project\Projet_Work\kaleads-atomic-agents"

# Activate venv
Write-Host "📦 Activation venv..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Set environment variables
Write-Host "🔐 Configuration variables d'environnement..." -ForegroundColor Yellow
$env:SUPABASE_URL="https://ckrspaktqohjenqfuuzl.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNrcnNwYWt0cW9oamVucWZ1dXpsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjYxNjQyMiwiZXhwIjoyMDc4MTkyNDIyfQ.uxZKZuCqZJnadg7ysnliZ5M4TfcKIl5jbW-eR1mpiBU"

# Start API
Write-Host "✅ Démarrage du serveur sur http://localhost:8001" -ForegroundColor Green
Write-Host "   - Health check: http://localhost:8001/health" -ForegroundColor Cyan
Write-Host "   - Docs API: http://localhost:8001/docs" -ForegroundColor Cyan
Write-Host "" 
Write-Host "Appuyez sur Ctrl+C pour arrêter" -ForegroundColor Gray
Write-Host ""

python -m uvicorn src.api.n8n_optimized_api:app --host 0.0.0.0 --port 8001 --reload
```

**Puis lancer**:
```powershell
.\start_api.ps1
```

---

## 🧪 Tester avec Python (Plus Facile)

Créer un fichier `test_api_quick.py`:

```python
"""Test rapide de l'API"""
import requests
import json

API_URL = "http://localhost:8001"
API_KEY = "lL^nc2U%tU8f2!LH48!29!mW8"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

print("🧪 Test 1: Health Check")
print("-" * 50)
response = requests.get(f"{API_URL}/health")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

print("\n🧪 Test 2: Coordinator Analyze")
print("-" * 50)
response = requests.post(
    f"{API_URL}/api/v2/coordinator/analyze",
    headers=headers,
    json={
        "client_id": "kaleads",
        "target_count": 500,
        "country": "France"
    }
)
print(f"Status: {response.status_code}")
result = response.json()

print(f"\n✅ Client: {result['client_name']}")
print(f"✅ Pain Type: {result['pain_type']}")
print(f"✅ Strategy: {result['strategy']}")
print(f"✅ Google Maps Searches: {len(result['google_maps_searches'])}")
print(f"✅ JobSpy Searches: {len(result['jobspy_searches'])}")
print(f"✅ Estimated Total Leads: {result['estimated_leads']['total']}")

# Save full response
with open("test_coordinator_result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"\n💾 Résultat complet sauvegardé dans: test_coordinator_result.json")
```

**Lancer**:
```powershell
python test_api_quick.py
```

---

## 🔧 Si l'API Ne Démarre Pas

### Problème: "Port 8001 already in use"

**Solution 1**: Tuer le processus
```powershell
Get-NetTCPConnection -LocalPort 8001 | ForEach-Object { 
    Stop-Process -Id $_.OwningProcess -Force 
}
```

**Solution 2**: Utiliser un autre port
```powershell
python -m uvicorn src.api.n8n_optimized_api:app --host 0.0.0.0 --port 8002 --reload
```

### Problème: "Module not found"

**Solution**: Réinstaller les dépendances
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install supabase
```

### Problème: "Supabase not configured"

**Solution**: Vérifier les variables d'environnement
```powershell
# Dans le même terminal où l'API tourne
echo $env:SUPABASE_URL
echo $env:SUPABASE_SERVICE_ROLE_KEY

# Si vides, les redéfinir
$env:SUPABASE_URL="https://ckrspaktqohjenqfuuzl.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY="eyJ..."
```

---

## 🎯 Tester dans n8n

### Étape 1: S'assurer que l'API tourne

```powershell
# Terminal 1: API
.\start_api.ps1

# Terminal 2: Test
curl http://localhost:8001/health
```

### Étape 2: Ouvrir n8n

Si n8n n'est pas encore installé:
```powershell
npx n8n
```

Puis ouvrir: `http://localhost:5678`

### Étape 3: Créer un workflow de test simple

**Node 1: Manual Trigger**
- Type: Manual Trigger

**Node 2: HTTP Request - Coordinator**
- Method: POST
- URL: `http://localhost:8001/api/v2/coordinator/analyze`
- Authentication: Header Auth
  - Name: `X-API-Key`
  - Value: `lL^nc2U%tU8f2!LH48!29!mW8`
- Body (JSON):
```json
{
  "client_id": "kaleads",
  "target_count": 500,
  "country": "France"
}
```

**Node 3: Set (pour visualiser)**
- Operations: Keep Only Set Fields
- Fields to Set:
  - `client_name` = `{{ $json.client_name }}`
  - `strategy` = `{{ $json.strategy }}`
  - `google_maps_count` = `{{ $json.google_maps_searches.length }}`
  - `jobspy_count` = `{{ $json.jobspy_searches.length }}`
  - `total_leads` = `{{ $json.estimated_leads.total }}`

**Exécuter le workflow** → Tu devrais voir les données Kaleads!

---

## 📊 Tester les 3 Endpoints Séparément

### 1. Coordinator (Génère la stratégie)

```powershell
curl -X POST http://localhost:8001/api/v2/coordinator/analyze `
  -H "Content-Type: application/json" `
  -H "X-API-Key: lL^nc2U%tU8f2!LH48!29!mW8" `
  -d '{\"client_id\": \"kaleads\", \"target_count\": 500}'
```

### 2. Google Maps (Scrape entreprises - DEMO MODE)

```powershell
curl -X POST http://localhost:8001/api/v2/leads/google-maps `
  -H "Content-Type: application/json" `
  -H "X-API-Key: lL^nc2U%tU8f2!LH48!29!mW8" `
  -d '{\"query\": \"agence SaaS\", \"cities\": [\"Paris\", \"Lyon\"], \"max_results_per_city\": 10}'
```

⚠️ **Note**: Google Maps nécessite une clé RapidAPI. En mode démo, tu auras des données simulées.

### 3. JobSpy (Scrape offres d'emploi - DEMO MODE)

```powershell
curl -X POST http://localhost:8001/api/v2/leads/jobspy `
  -H "Content-Type: application/json" `
  -H "X-API-Key: lL^nc2U%tU8f2!LH48!29!mW8" `
  -d '{\"job_title\": \"Head of Sales\", \"location\": \"France\", \"company_size\": [\"11-50\", \"51-200\"], \"max_results\": 20}'
```

⚠️ **Note**: JobSpy nécessite un serveur JobSpy tournant. En mode démo, tu auras des données simulées.

---

## 🎯 Workflow n8n Complet - Test Minimal

### Créer ce workflow dans n8n:

```
[Manual Trigger]
      ↓
[HTTP Request - Coordinator]
  URL: http://localhost:8001/api/v2/coordinator/analyze
  Body: {"client_id": "kaleads", "target_count": 500}
      ↓
[Function - Extract First Search]
  Code:
  const firstGmapsSearch = $input.item.json.google_maps_searches[0];
  return { json: firstGmapsSearch };
      ↓
[HTTP Request - Google Maps]
  URL: http://localhost:8001/api/v2/leads/google-maps
  Body: 
  {
    "query": "{{ $json.query }}",
    "cities": {{ $json.cities }},
    "max_results_per_city": 10
  }
      ↓
[Code - Show Results]
  Code:
  const leads = $input.item.json.leads || [];
  console.log(`Found ${leads.length} leads`);
  return leads.map(lead => ({ json: lead }));
```

**Exécuter** → Tu devrais voir des leads apparaître!

---

## 📝 Checklist de Test

- [ ] API démarre sans erreur
- [ ] Health check retourne `"status": "healthy"`
- [ ] Coordinator retourne `"client_name": "Kaleads"`
- [ ] Coordinator retourne `"strategy": "hybrid"`
- [ ] Google Maps searches contient ~5 queries
- [ ] JobSpy searches contient ~3 queries
- [ ] n8n peut se connecter à l'API
- [ ] n8n reçoit les données correctement

---

## 🚀 Une Fois que Tout Fonctionne

1. **Importer le workflow complet**: `n8n_workflows/lead_generation_master.json`
2. **Créer les Google Sheets** avec les templates
3. **Configurer les Sheet IDs** dans n8n
4. **Lancer le workflow complet** → Attendre 30 min
5. **Vérifier les Google Sheets** → Elles se remplissent!

---

## 💡 Commandes Utiles

### Voir les logs de l'API en temps réel
```powershell
# L'API affiche les logs dans le terminal où elle tourne
# Regarder les lignes avec "DEBUG:" pour voir les requêtes Supabase
```

### Sauvegarder la config dans un .env (optionnel)
```powershell
# Créer un fichier .env
@"
SUPABASE_URL=https://ckrspaktqohjenqfuuzl.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNrcnNwYWt0cW9oamVucWZ1dXpsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjYxNjQyMiwiZXhwIjoyMDc4MTkyNDIyfQ.uxZKZuCqZJnadg7ysnliZ5M4TfcKIl5jbW-eR1mpiBU
"@ | Out-File -FilePath .env -Encoding UTF8

# Puis installer python-dotenv
pip install python-dotenv

# L'API chargera automatiquement les variables du .env
```

### Vérifier que Supabase fonctionne
```powershell
python -c "from src.providers.supabase_client import SupabaseClient; import os; os.environ['SUPABASE_URL']='https://ckrspaktqohjenqfuuzl.supabase.co'; os.environ['SUPABASE_SERVICE_ROLE_KEY']='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNrcnNwYWt0cW9oamVucWZ1dXpsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjYxNjQyMiwiZXhwIjoyMDc4MTkyNDIyfQ.uxZKZuCqZJnadg7ysnliZ5M4TfcKIl5jbW-eR1mpiBU'; client = SupabaseClient(); print(f'Supabase enabled: {client.enabled}')"
```

---

## 🎓 Prochaines Étapes

Une fois que l'API fonctionne et que tu as testé les endpoints:

1. ✅ Setup Google Sheets (templates dans `n8n_workflows/GOOGLE_SHEETS_TEMPLATES.md`)
2. ✅ Importer workflow n8n (`n8n_workflows/lead_generation_master.json`)
3. ✅ Configurer credentials n8n (API Key + Google OAuth)
4. ✅ Lancer workflow complet
5. ✅ Vérifier résultats dans Google Sheets
6. ✅ Setup enrichissement (Clay/Phantombuster)

**Tout est documenté dans `QUICK_START_N8N.md`!**


