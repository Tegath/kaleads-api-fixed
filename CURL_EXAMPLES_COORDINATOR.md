# 🧪 Exemples curl - Lead Gen Coordinator

Exemples de requêtes pour tester les nouveaux endpoints du coordinateur.

---

## 🏥 Health Check

```bash
curl -X GET http://localhost:8001/health
```

**Production:**
```bash
curl -X GET http://92.112.193.183:20001/health
```

---

## 📊 Endpoint 1: Coordinator Analyze

Analyse le contexte client Kaleads et génère une stratégie complète.

### Local

```bash
curl -X POST http://localhost:8001/api/v2/coordinator/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key" \
  -d '{
    "client_id": "kaleads",
    "target_count": 500,
    "country": "France"
  }'
```

### Production

```bash
curl -X POST http://92.112.193.183:20001/api/v2/coordinator/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key" \
  -d '{
    "client_id": "kaleads",
    "target_count": 500,
    "country": "France"
  }'
```

### Avec régions spécifiques

```bash
curl -X POST http://localhost:8001/api/v2/coordinator/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key" \
  -d '{
    "client_id": "kaleads",
    "target_count": 1000,
    "regions": ["Île-de-France", "Auvergne-Rhône-Alpes"],
    "country": "France"
  }'
```

### Réponse attendue

```json
{
  "success": true,
  "client_name": "Kaleads",
  "pain_type": "lead_generation",
  "strategy": "hybrid",
  "google_maps_searches": [
    {
      "query": "agence marketing digital",
      "cities": ["Paris", "Lyon", "Marseille", ...],
      "max_results_per_city": 50
    },
    {
      "query": "agence SaaS",
      "cities": ["Paris", "Lyon", "Marseille", ...],
      "max_results_per_city": 50
    }
  ],
  "jobspy_searches": [
    {
      "job_title": "Head of Sales",
      "location": "France",
      "company_size": ["11-50", "51-200", "201-500"],
      "max_results": 100
    },
    {
      "job_title": "VP Marketing",
      "location": "France",
      "company_size": ["11-50", "51-200", "201-500"],
      "max_results": 100
    }
  ],
  "cities": ["Paris", "Lyon", "Marseille", "Toulouse", ...],
  "estimated_leads": {
    "google_maps": 500,
    "jobspy": 200,
    "total": 700
  },
  "execution_plan": {
    "step_1": "Execute Google Maps searches in parallel",
    "step_2": "Execute JobSpy searches in parallel",
    "step_3": "Deduplicate companies",
    "step_4": "Feed to email generation pipeline"
  }
}
```

---

## 🗺️ Endpoint 2: Google Maps Search

Exécute une recherche Google Maps sur plusieurs villes.

### Local

```bash
curl -X POST http://localhost:8001/api/v2/leads/google-maps \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key" \
  -d '{
    "query": "agence marketing digital",
    "cities": ["Paris", "Lyon", "Marseille"],
    "max_results_per_city": 50
  }'
```

### Production

```bash
curl -X POST http://92.112.193.183:20001/api/v2/leads/google-maps \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key" \
  -d '{
    "query": "agence marketing digital",
    "cities": ["Paris", "Lyon", "Marseille"],
    "max_results_per_city": 50
  }'
```

### Réponse attendue

```json
{
  "success": true,
  "leads": [
    {
      "company_name": "Agence Digitale Paris",
      "address": "12 Rue de Rivoli, 75001 Paris",
      "phone": "+33 1 23 45 67 89",
      "website": "https://agence-digitale.fr",
      "rating": 4.5,
      "reviews_count": 120,
      "city": "Paris",
      "source": "google_maps"
    },
    ...
  ],
  "total_leads": 150,
  "cities_searched": ["Paris", "Lyon", "Marseille"],
  "cost_usd": 0.003
}
```

---

## 💼 Endpoint 3: JobSpy Search

Exécute une recherche JobSpy pour détecter les signaux d'embauche.

### Local

```bash
curl -X POST http://localhost:8001/api/v2/leads/jobspy \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key" \
  -d '{
    "job_title": "Head of Sales",
    "location": "France",
    "company_size": ["11-50", "51-200"],
    "industries": ["SaaS", "Tech"],
    "max_results": 100
  }'
```

### Production

```bash
curl -X POST http://92.112.193.183:20001/api/v2/leads/jobspy \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key" \
  -d '{
    "job_title": "Head of Sales",
    "location": "France",
    "company_size": ["11-50", "51-200"],
    "industries": ["SaaS", "Tech"],
    "max_results": 100
  }'
```

### Réponse attendue

```json
{
  "success": true,
  "leads": [
    {
      "company_name": "Aircall",
      "job_title": "Head of Sales France",
      "location": "Paris",
      "company_size": "51-200",
      "company_website": "https://aircall.io",
      "hiring_signal": "Recruiting for Head of Sales",
      "job_posted_date": "2025-01-10",
      "job_url": "https://...",
      "industry": "SaaS",
      "source": "jobspy"
    },
    ...
  ],
  "total_leads": 45,
  "job_title_searched": "Head of Sales",
  "cost_usd": 0.0005
}
```

---

## 🔄 Workflow n8n complet

### Étape 1: Analyser le contexte client

```bash
curl -X POST http://92.112.193.183:20001/api/v2/coordinator/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key" \
  -d '{
    "client_id": "kaleads",
    "target_count": 500,
    "country": "France"
  }' > strategy.json
```

### Étape 2: Exécuter les recherches Google Maps (en parallèle)

```bash
# Pour chaque google_maps_searches dans strategy.json
curl -X POST http://92.112.193.183:20001/api/v2/leads/google-maps \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key" \
  -d '{
    "query": "agence marketing digital",
    "cities": ["Paris", "Lyon", "Marseille"],
    "max_results_per_city": 50
  }' > gmaps_leads_1.json
```

### Étape 3: Exécuter les recherches JobSpy (en parallèle)

```bash
# Pour chaque jobspy_searches dans strategy.json
curl -X POST http://92.112.193.183:20001/api/v2/leads/jobspy \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key" \
  -d '{
    "job_title": "Head of Sales",
    "location": "France",
    "company_size": ["11-50", "51-200"],
    "max_results": 100
  }' > jobspy_leads_1.json
```

### Étape 4: Générer les emails

```bash
# Pour chaque lead collecté
curl -X POST http://92.112.193.183:20001/api/v2/generate-email \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key" \
  -d '{
    "client_id": "kaleads",
    "contact": {
      "company_name": "Aircall",
      "first_name": "Sophie",
      "website": "https://aircall.io",
      "industry": "SaaS"
    },
    "template_name": "outreach_signal_v1",
    "options": {
      "model_preference": "quality",
      "enable_scraping": true,
      "enable_tavily": true
    }
  }'
```

---

## 🧪 Test rapide

Tester que tout fonctionne:

```bash
# 1. Health check
curl http://localhost:8001/health

# 2. Coordinator analyze
curl -X POST http://localhost:8001/api/v2/coordinator/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key" \
  -d '{"client_id": "kaleads", "target_count": 500, "country": "France"}' | jq

# 3. Si le test 2 fonctionne, tout est bon! 🎉
```

---

## 📝 Notes

### Configuration requise

- **Supabase**: Client "kaleads" doit exister dans la table `clients`
- **Cities Database**: Le fichier `data/cities_database.json` doit être présent
- **RapidAPI (optionnel)**: Pour Google Maps (endpoint /leads/google-maps)
- **JobSpy API (optionnel)**: Pour JobSpy (endpoint /leads/jobspy)

### Variables d'environnement

```bash
API_KEY=your-secure-api-key
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-supabase-key
RAPIDAPI_KEY=your-rapidapi-key  # Pour Google Maps
JOBSPY_API_URL=http://localhost:8000  # Pour JobSpy
```

---

**Happy Testing! 🚀**
