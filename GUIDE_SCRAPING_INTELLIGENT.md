# 🚀 Guide : Scraping Intelligent avec Background Jobs

## 🎯 Le Problème Résolu

Avant, tu devais :
- ❌ Gérer manuellement la liste des villes
- ❌ Risquer de perdre toutes les données en cas de timeout
- ❌ Payer pour scraper des petites villes peu rentables
- ❌ Attendre que tout soit fini avant d'avoir des résultats

Maintenant, le système :
- ✅ **Choisit automatiquement** les villes à scraper selon leur population
- ✅ **Sauvegarde les leads au fur et à mesure** (toutes les 100 leads)
- ✅ **Continue en background** même si tu fermes n8n
- ✅ **Peut reprendre** où il s'est arrêté en cas d'interruption
- ✅ **Te montre la progression en temps réel**

---

## 📊 Stratégie Intelligente par Population

### Niveaux de Priorité

| Priorité | Population | Max Pages | Stratégie | Exemple |
|----------|------------|-----------|-----------|---------|
| **1 - HIGH** | > 100 000 hab | 10 pages | Comprehensive | Paris, Lyon, Marseille |
| **2 - MEDIUM** | 20k - 100k | 5 pages | Moderate | Angers, Brest, Reims |
| **3 - LOW** | 5k - 20k | 2 pages | Light | Vitré, Concarneau |
| **SKIP** | < 5 000 hab | 0 pages | Skip | Petits villages |

### Exemples de Coûts

**Scraping "agence marketing" avec max_priority=1 (seulement >100k hab)**
- Villes : ~150
- Leads estimés : ~22 500
- Coût : ~$11
- Temps : ~25 minutes

**Scraping "agence marketing" avec max_priority=2 (>20k hab)**
- Villes : ~900
- Leads estimés : ~67 500
- Coût : ~$34
- Temps : ~90 minutes

**Scraping "agence marketing" avec max_priority=3 (>5k hab)**
- Villes : ~3 500
- Leads estimés : ~122 000
- Coût : ~$61
- Temps : ~170 minutes

---

## 🛠️ Utilisation Simple

### Méthode 1 : Call HTTP Direct (Recommandé)

#### Lancer un scraping

```http
POST http://92.112.193.183:20001/api/v2/scraping/start
Headers: X-API-Key: lL^nc2U%tU8f2!LH48!29!mW8

Params:
?query=agence marketing
&max_priority=2
&country=France
```

**Response :**
```json
{
  "job_id": "abc-123-def",
  "status": "pending",
  "estimated_cities": 900,
  "estimated_cost_usd": 34.50,
  "message": "Job started. Monitor at /api/v2/scraping/status/abc-123-def"
}
```

#### Voir la progression

```http
GET http://92.112.193.183:20001/api/v2/scraping/status/abc-123-def
Headers: X-API-Key: lL^nc2U%tU8f2!LH48!29!mW8
```

**Response :**
```json
{
  "job_id": "abc-123-def",
  "status": "running",
  "progress_pct": 45.5,
  "cities_completed": 410,
  "total_cities": 900,
  "total_leads_found": 28 450,
  "current_city": "Lyon",
  "estimated_cost_usd": 34.50
}
```

#### Voir tous les jobs

```http
GET http://92.112.193.183:20001/api/v2/scraping/jobs?status=running
Headers: X-API-Key: lL^nc2U%tU8f2!LH48!29!mW8
```

**Response :**
```json
{
  "jobs": [
    {
      "job_id": "abc-123",
      "query": "agence marketing",
      "status": "running",
      "progress_pct": 45.5,
      "total_leads_found": 28450
    },
    {
      "job_id": "def-456",
      "query": "startup SaaS",
      "status": "completed",
      "progress_pct": 100,
      "total_leads_found": 12890
    }
  ]
}
```

---

## 🔄 Reprendre un Job Interrompu

Si le serveur plante, le Docker redémarre, ou que tu stoppes un job :

```http
POST http://92.112.193.183:20001/api/v2/scraping/resume/abc-123-def
Headers: X-API-Key: lL^nc2U%tU8f2!LH48!29!mW8
```

Le job reprendra **exactement où il s'était arrêté** !

---

## 📖 Workflow n8n Recommandé

### Node 1 : Start Scraping Job

**Type** : HTTP Request
**URL** : `http://kaleads-atomic-agents:20001/api/v2/scraping/start`
**Method** : POST
**Headers** : `X-API-Key: lL^nc2U%tU8f2!LH48!29!mW8`
**Query Params** :
```
query: {{ $json.search_query }}
max_priority: 2
country: France
```

### Node 2 : Wait 5 seconds

**Type** : Wait
**Time** : 5 seconds

### Node 3 : Check Job Status (Loop)

**Type** : HTTP Request
**URL** : `http://kaleads-atomic-agents:20001/api/v2/scraping/status/{{ $json.job_id }}`
**Method** : GET
**Headers** : `X-API-Key: lL^nc2U%tU8f2!LH48!29!mW8`

### Node 4 : IF Status == "completed"

**Type** : IF
**Condition** : `{{ $json.status }} == "completed"`

- **TRUE** → Continue workflow (load leads from Supabase)
- **FALSE** → Wait 30s and loop back to Node 3

### Node 5 : Load Leads from Supabase

**Type** : Supabase Query
**Table** : `leads`
**Filter** : `source = 'google_maps' AND client_id = 'kaleads'`
**Order** : `created_at DESC`
**Limit** : 1000

### Node 6 : Email Generation

Feed les leads à ton système d'email generation !

---

## ⚙️ Configuration Avancée

### Paramètres Disponibles

| Paramètre | Description | Défaut | Valeurs |
|-----------|-------------|--------|---------|
| `query` | Requête de recherche | Required | "agence marketing" |
| `country` | Pays | "France" | "France", "Wallonie" |
| `min_population` | Pop minimale | 5000 | 1000-50000 |
| `max_priority` | Priorité max | 3 | 1 (HIGH), 2 (MEDIUM), 3 (ALL) |
| `client_id` | ID client Supabase | "kaleads" | Any string |

### Exemples d'Usage

**Scraping rapide (grandes villes uniquement)**
```
?query=agence+web&max_priority=1
→ ~150 villes, ~$11, ~25 min
```

**Scraping complet (toutes villes >5k hab)**
```
?query=agence+marketing&max_priority=3
→ ~3500 villes, ~$61, ~170 min
```

**Scraping Wallonie**
```
?query=startup+tech&country=Wallonie&max_priority=3
→ ~100 villes, ~$5, ~15 min
```

**Scraping ultra-sélectif (>50k hab)**
```
?query=cabinet+avocat&min_population=50000&max_priority=2
→ ~80 villes, ~$8, ~18 min
```

---

## 🎯 Monitoring en Temps Réel

### Query Supabase pour voir les jobs actifs

```sql
SELECT
  id,
  query,
  status,
  ROUND((cities_completed::float / total_cities::float) * 100, 2) as progress_pct,
  total_leads_found,
  current_city,
  estimated_cost_usd,
  created_at
FROM scraping_jobs
WHERE status IN ('pending', 'running')
ORDER BY created_at DESC;
```

### Query pour voir les leads du dernier scraping

```sql
SELECT
  company_name,
  city,
  phone,
  website,
  created_at
FROM leads
WHERE client_id = 'kaleads'
  AND source = 'google_maps'
  AND created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC
LIMIT 100;
```

### Query pour statistiques par ville

```sql
SELECT
  city,
  COUNT(*) as lead_count,
  COUNT(DISTINCT company_name) as unique_companies
FROM leads
WHERE client_id = 'kaleads'
  AND source = 'google_maps'
GROUP BY city
ORDER BY lead_count DESC
LIMIT 20;
```

---

## 🔧 Setup Initial (Une Fois)

### Étape 1 : Créer les tables Supabase

Exécuter ces 2 scripts SQL dans Supabase :

1. [supabase_leads_table.sql](supabase_leads_table.sql)
   - Table `leads` pour stocker tous les leads
2. [supabase_scraping_jobs_table.sql](supabase_scraping_jobs_table.sql)
   - Table `scraping_jobs` pour tracker les jobs
   - Table `city_strategy` pour la stratégie par ville

### Étape 2 : Vérifier les CSV

Ces fichiers doivent être dans le Docker :
- ✅ `Villes_france.csv` (~36k villes)
- ✅ `Villes_belgique.csv` (~262 villes)
- ✅ `Population_villes_france.csv` (données de population)

Vérifier :
```bash
docker exec kaleads-atomic-agents ls -lh *.csv
```

### Étape 3 : Tester avec une petite query

```bash
curl -X POST "http://92.112.193.183:20001/api/v2/scraping/start?query=test&max_priority=1" \
  -H "X-API-Key: lL^nc2U%tU8f2!LH48!29!mW8"
```

---

## 📈 Optimisations Recommandées

### 1. Scraper par Tranches

Au lieu de tout scraper d'un coup, scrape par priorité :

**Jour 1** : Scrape HIGH (max_priority=1)
```
POST /api/v2/scraping/start?query=agence+marketing&max_priority=1
→ ~150 villes, ~$11, ~25 min
```

**Jour 2** : Si besoin de plus, scrape MEDIUM (max_priority=2)
```
POST /api/v2/scraping/start?query=agence+marketing&max_priority=2
→ ~900 villes, ~$34, ~90 min
```

**Jour 3** : Si toujours besoin, scrape ALL (max_priority=3)
```
POST /api/v2/scraping/start?query=agence+marketing&max_priority=3
→ ~3500 villes, ~$61, ~170 min
```

### 2. Analyser le ROI Avant de Continuer

Après chaque tranche, vérifie le taux de conversion :

```sql
SELECT
  CASE
    WHEN population >= 100000 THEN 'HIGH'
    WHEN population >= 20000 THEN 'MEDIUM'
    ELSE 'LOW'
  END as priority,
  COUNT(*) as total_leads,
  COUNT(*) FILTER (WHERE email IS NOT NULL) as leads_with_email,
  ROUND(COUNT(*) FILTER (WHERE email IS NOT NULL)::float / COUNT(*)::float * 100, 2) as email_pct
FROM leads
LEFT JOIN city_strategy USING (city_name)
WHERE client_id = 'kaleads'
GROUP BY 1
ORDER BY 1;
```

Si le priority LOW a un mauvais ROI → arrête là, pas besoin de scraper les petites villes !

---

## 🐛 Troubleshooting

### Job bloqué en "running"

```sql
-- Voir le dernier checkpoint
SELECT last_checkpoint, current_city, updated_at
FROM scraping_jobs
WHERE id = 'job-id-here';

-- Si bloqué depuis >1h, reprendre
```

```http
POST /api/v2/scraping/resume/job-id-here
```

### Pas de leads sauvegardés

Vérifier les RLS policies dans Supabase :
```sql
-- Désactiver temporairement pour debug
ALTER TABLE leads DISABLE ROW LEVEL SECURITY;
```

### Job failed avec erreur "RapidAPI"

Vérifier le quota RapidAPI :
- Aller sur https://rapidapi.com/dashboard
- Vérifier les calls restants
- Augmenter le plan si nécessaire

---

## 💡 Cas d'Usage

### Cas 1 : Prospection Rapide (1 Query)

**Objectif** : 1000 leads de qualité rapidement

```http
POST /api/v2/scraping/start
?query=agence+marketing
&max_priority=1
&min_population=50000
```

→ ~80 villes, ~$8, ~18 minutes, ~1200 leads

### Cas 2 : Base de Données Complète (Multiple Queries)

**Objectif** : Base de 50k+ leads pour campagnes longue durée

Lancer 5 jobs en parallèle :
```
Job 1: "agence marketing digital" - max_priority=2
Job 2: "startup SaaS" - max_priority=2
Job 3: "agence web" - max_priority=2
Job 4: "éditeur logiciel" - max_priority=2
Job 5: "entreprise technologique" - max_priority=3
```

Total : ~250k leads, ~$150, ~6 heures

### Cas 3 : Ciblage Géographique

**Objectif** : Leads en Wallonie uniquement

```http
POST /api/v2/scraping/start
?query=bureau+comptable
&country=Wallonie
&max_priority=3
```

→ ~100 villes, ~$5, ~15 minutes, ~1500 leads

---

## 🎉 Résumé

**Tu dis simplement** :
```
"Scrape 'agence marketing' dans les villes moyennes"
```

**Le système fait** :
1. ✅ Charge les 36k villes depuis les CSV
2. ✅ Filtre avec stratégie intelligente (900 villes >20k hab)
3. ✅ Scrape 5 pages pour les grandes villes, 2 pour les petites
4. ✅ Sauvegarde au fur et à mesure en Supabase
5. ✅ S'arrête automatiquement quand plus de résultats (économise l'API)
6. ✅ Te donne la progression en temps réel
7. ✅ Peut reprendre si interruption

**Tu récupères** :
- 67 500 leads dédupliqués
- Coût : $34
- Temps : 90 minutes
- Stockés en Supabase, prêts pour l'email gen !

---

## 📞 Commandes Utiles

```bash
# Voir les logs en temps réel
docker logs -f kaleads-atomic-agents

# Voir uniquement les logs de scraping
docker logs -f kaleads-atomic-agents 2>&1 | grep "Scraping"

# Redémarrer l'API
docker-compose restart

# Rebuild complet
cd /opt/kaleads-api && git pull && docker-compose up -d --build
```

**Bon scraping intelligent ! 🚀**
