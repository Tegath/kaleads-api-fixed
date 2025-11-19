# Guide Complet : Scraping Économique de Toutes les Villes

## 🎯 Vue d'ensemble

Le système a été modifié pour scraper **TOUTES les villes de France et Wallonie** de manière économique avec :
- ✅ **Pagination intelligente** : s'arrête automatiquement quand plus de résultats
- ✅ **Déduplication automatique** : évite les doublons en base Supabase
- ✅ **Stockage persistant** : tous les leads sont sauvegardés pour réutilisation
- ✅ **Mode comprehensive** : scraping complet one-time pour Google Maps
- ✅ **Mode journalier/hebdomadaire** : pour JobSpy (offres d'emploi)

---

## 📊 Statistiques

### Villes disponibles
- **France** : ~35 000 villes
- **Wallonie** : ~262 villes
- **Total** : ~35 262 villes

### Estimation pour une recherche complète
- **Query** : "agence marketing"
- **Villes** : 35 262
- **Résultats estimés par ville** : 10-30 (moyenne 20)
- **Total leads estimés** : ~700 000 leads
- **Temps estimé** : 245 heures (~10 jours en background)
- **Coût RapidAPI estimé** : ~$350 (à $0.001/page, ~350k pages)

---

## 🛠️ Étape 1 : Créer la table Supabase

### 1.1 Accéder à Supabase SQL Editor
1. Aller sur https://supabase.com/dashboard
2. Sélectionner votre projet
3. Aller dans **SQL Editor**

### 1.2 Exécuter le script SQL
Copier-coller le contenu de [`supabase_leads_table.sql`](supabase_leads_table.sql) et exécuter.

Cela va créer :
- ✅ Table `leads` avec déduplication (lead_hash unique)
- ✅ Index pour requêtes rapides
- ✅ RLS policies
- ✅ Trigger auto-update `updated_at`

### 1.3 Vérifier la création
```sql
SELECT COUNT(*) FROM leads; -- Devrait retourner 0 (table vide)
```

---

## 🚀 Étape 2 : Workflow n8n - Mode Comprehensive

### Architecture du workflow

```
┌─────────────────┐
│ 1. Coordinator  │ → Génère stratégie avec ALL_CITIES
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Google Maps  │ → Scrape TOUTES les villes + pagination intelligente
│    Comprehensive│ → Stocke en Supabase avec déduplication
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. JobSpy       │ → Recherche offres d'emploi (journalier/hebdomadaire)
│    (Optional)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Email Gen    │ → Génère emails pour les leads qualifiés
└─────────────────┘
```

### Node 1 : HTTP Request - Coordinator

**Settings:**
- **URL** : `http://kaleads-atomic-agents:20001/api/v2/coordinator/analyze`
- **Method** : POST
- **Headers** : `X-API-Key: lL^nc2U%tU8f2!LH48!29!mW8`
- **Body JSON** :
```json
{
  "client_id": "kaleads",
  "target_count": 500000,
  "country": "France"
}
```

**Response attendue** :
```json
{
  "pain_type": "lead_generation",
  "strategy": "hybrid",
  "google_maps_searches": [
    {
      "query": "agence marketing digital",
      "cities": "ALL_CITIES",
      "country": "France",
      "use_pagination": true,
      "comprehensive": true
    },
    // ... 4 autres queries
  ],
  "execution_plan": {
    "mode": "COMPREHENSIVE_SCRAPING",
    "cities_count": 35262,
    "estimated_time": "245 hours (background process)"
  }
}
```

---

### Node 2 : Split In Batches - Google Maps Searches

**Settings:**
- **Batch Size** : 1
- **Input Field** : `google_maps_searches`

---

### Node 3 : HTTP Request - Execute Google Maps (Comprehensive)

**IMPORTANT** : Ce call va prendre des HEURES à compléter. Il faut le lancer en mode background.

**Settings:**
- **URL** : `http://kaleads-atomic-agents:20001/api/v2/leads/google-maps`
- **Method** : POST
- **Headers** : `X-API-Key: lL^nc2U%tU8f2!LH48!29!mW8`
- **Timeout** : 86400000 (24 heures en ms)
- **Body JSON** :
```json
{
  "query": "{{ $json.query }}",
  "cities": "{{ $json.cities }}",
  "country": "{{ $json.country }}",
  "use_pagination": {{ $json.use_pagination }},
  "comprehensive": {{ $json.comprehensive }},
  "client_id": "kaleads"
}
```

**Ce que fait ce call** :
1. Charge TOUTES les villes depuis les CSV
2. Pour chaque ville :
   - Lance une recherche Google Maps
   - Pagination intelligente (continue jusqu'à plus de résultats)
   - Déduplication en mémoire
3. Stocke TOUS les leads en Supabase
4. Retourne les statistiques

**Response attendue** :
```json
{
  "success": true,
  "leads": [...],  // Peut être vide si comprehensive=true (stocké en DB)
  "total_leads": 123456,
  "cities_searched": ["ALL_CITIES"],
  "cost_usd": 12.34
}
```

---

### Node 4 : Alternative - Mode Background (Recommandé)

**Problème** : n8n va timeout après 24h même avec timeout max.

**Solution** : Créer un endpoint séparé qui lance le scraping en background.

#### Option A : Webhook Trigger + Background Task

1. Créer un webhook n8n qui déclenche le scraping
2. Le scraping se fait en background sur le serveur
3. n8n reçoit immédiatement une réponse "Job started"
4. Le scraping continue pendant des jours si nécessaire
5. Les résultats sont stockés en Supabase au fur et à mesure

#### Option B : Cron Job quotidien

Lancer le scraping par batches :
- Jour 1 : Villes A-D (7000 villes)
- Jour 2 : Villes E-L (7000 villes)
- Jour 3 : Villes M-R (7000 villes)
- Etc.

---

## 📈 Étape 3 : Monitoring et Queries Supabase

### Compter les leads scrapés en temps réel

```sql
SELECT
  source,
  COUNT(*) as total_leads,
  COUNT(DISTINCT city) as cities_covered
FROM leads
WHERE client_id = 'kaleads'
GROUP BY source;
```

### Top 10 villes avec le plus de leads

```sql
SELECT
  city,
  COUNT(*) as lead_count
FROM leads
WHERE client_id = 'kaleads' AND source = 'google_maps'
GROUP BY city
ORDER BY lead_count DESC
LIMIT 10;
```

### Progression du scraping (nouveaux leads par heure)

```sql
SELECT
  DATE_TRUNC('hour', created_at) as hour,
  COUNT(*) as leads_added
FROM leads
WHERE client_id = 'kaleads'
GROUP BY hour
ORDER BY hour DESC
LIMIT 24;
```

---

## 💰 Optimisation des Coûts

### Stratégie 1 : Filtrer les villes par taille
Ne scraper que les villes > 1000 habitants pour économiser ~90% des calls.

**Modifier** [`cities_loader.py`](src/helpers/cities_loader.py) pour filtrer :
```python
def get_all_cities(self, country: str = "France", min_population: int = 1000) -> List[str]:
    # Filtrer par population si CSV a cette info
    pass
```

### Stratégie 2 : Limiter les pages par ville
Au lieu de scraper TOUTES les pages, limiter à 5 pages max par ville.

**Modifier** dans [`google_maps_integration.py`](kaleads-atomic-agents/src/integrations/google_maps_integration.py:214) :
```python
# Safety: max 5 pages per city for cost control
if page > 5:
    logger.warning(f"Reached max page limit (5) for {city}")
    break
```

### Stratégie 3 : Scraping intelligent par priorité
1. Scraper d'abord les **grandes villes** (Paris, Lyon, etc.)
2. Analyser le taux de conversion
3. Si bon ROI → continuer avec petites villes
4. Si mauvais ROI → arrêter

---

## 🔄 Mode Journalier/Hebdomadaire pour JobSpy

JobSpy devrait être lancé régulièrement car les offres d'emploi changent souvent.

### Workflow séparé : JobSpy Daily Refresh

**Cron** : Tous les jours à 6h du matin
**Node 1** : HTTP Request - Coordinator (même qu'avant)
**Node 2** : Split In Batches - JobSpy Searches
**Node 3** : HTTP Request - Execute JobSpy
```json
{
  "job_title": "{{ $json.job_title }}",
  "location": "{{ $json.location }}",
  "company_size": {{ $json.company_size }},
  "industries": {{ $json.industries }},
  "max_results": {{ $json.max_results }}
}
```

---

## 🐛 Debugging et Logs

### Voir les logs du scraping en temps réel

```bash
# SSH sur le serveur
ssh root@92.112.193.183

# Voir les logs Docker
docker logs -f kaleads-atomic-agents

# Filtrer pour voir uniquement le scraping
docker logs -f kaleads-atomic-agents 2>&1 | grep "google_maps"
```

### Vérifier l'état du scraping

```bash
# Compter les leads en DB
curl -X POST https://your-supabase.supabase.co/rest/v1/rpc/count_leads \
  -H "apikey: YOUR_SUPABASE_ANON_KEY" \
  -H "Authorization: Bearer YOUR_SUPABASE_ANON_KEY"
```

---

## 📝 Checklist avant de lancer le scraping complet

- [ ] Table `leads` créée dans Supabase
- [ ] RLS policies configurées
- [ ] Index créés pour performance
- [ ] CSV des villes présents dans le projet
- [ ] RapidAPI key configurée dans .env
- [ ] Budget RapidAPI vérifié (~$350 nécessaire)
- [ ] Workflow n8n testé avec 3 villes
- [ ] Logs monitoring configurés
- [ ] Plan de backup des données Supabase

---

## 🎯 Exemple : Workflow n8n Simplifié

Pour éviter la complexité, voici un workflow minimaliste :

### Option Simple : Script Python Background

Au lieu d'utiliser n8n pour un scraping de plusieurs jours, créer un script Python standalone :

```python
# comprehensive_scraper.py
from src.integrations.google_maps_integration import GoogleMapsLeadGenerator
from src.providers.leads_storage import LeadsStorage

gmaps = GoogleMapsLeadGenerator()
storage = LeadsStorage(client_id="kaleads")

# Scrape comprehensive
queries = [
    "agence marketing digital",
    "startup SaaS",
    "agence web",
    "éditeur de logiciel",
    "entreprise technologique"
]

for query in queries:
    print(f"Scraping: {query}")
    leads = gmaps.search_all_cities_comprehensive(
        query=query,
        country="France"
    )

    stats = storage.store_leads(leads)
    print(f"✅ {query}: {stats}")
```

**Lancer en background** :
```bash
nohup python comprehensive_scraper.py > scraping.log 2>&1 &
```

**Avantages** :
- ✅ Pas de timeout n8n
- ✅ Logs clairs
- ✅ Peut tourner pendant des jours
- ✅ Résultats en Supabase accessibles immédiatement

---

## 📞 Support

Si des erreurs surviennent :
1. Vérifier les logs Docker
2. Vérifier Supabase (table accessible ?)
3. Vérifier RapidAPI (quota restant ?)
4. Tester avec 1 ville d'abord

**Bon scraping! 🚀**
