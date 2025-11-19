# 🎯 Plan Complet: Agent Coordinateur de Lead Generation

## Vision

Un **Agent Coordinateur intelligent** qui analyse le contexte client (depuis Supabase) et génère automatiquement les recherches optimales pour remplir des tables de leads via:
- Google Maps Scraper (entreprises locales)
- JobSpy (offres d'emploi / hiring signals)
- LinkedIn Scraper (futur)

---

## Architecture Globale

```
┌─────────────────────────────────────────────────────────────┐
│                    n8n Workflow                             │
├─────────────────────────────────────────────────────────────┤
│  1. Trigger (manual / cron)                                 │
│  2. Call → /api/v2/coordinator/analyze                      │
│     Input: { client_id: "kaleads" }                         │
│  3. Receive → Optimized search parameters                   │
│  4. Loop over Google Maps searches                          │
│  5. Loop over JobSpy searches                               │
│  6. Aggregate → Fill Google Sheets                          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│         kaleads-atomic-agents API (Coordinator)             │
├─────────────────────────────────────────────────────────────┤
│  Load ClientContext from Supabase                           │
│  ↓                                                           │
│  LeadGenCoordinator Agent analyzes:                         │
│    - ICP (target industries, company sizes, regions)        │
│    - Pain points solved                                     │
│    - Offerings                                              │
│  ↓                                                           │
│  Generate optimized search strategies:                      │
│    - Google Maps keywords per city                          │
│    - JobSpy search terms per region                         │
│    - LinkedIn filters (future)                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    External Scrapers                        │
├─────────────────────────────────────────────────────────────┤
│  • Google Maps Scraper (RapidAPI)                           │
│  • JobSpy API (local deployment)                            │
│  • LinkedIn Scraper (future)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Agent Coordinateur Core (LeadGenCoordinator)

### 1.1. Création de l'Agent

**Fichier**: `src/agents/lead_gen_coordinator_agent.py`

**Responsabilités**:
- Analyser le contexte client depuis Supabase
- Déterminer les meilleures stratégies de recherche
- Générer les mots-clés optimaux pour chaque scraper
- Retourner des paramètres structurés pour n8n

**Input Schema**:
```python
class LeadGenCoordinatorInputSchema(BaseIOSchema):
    client_id: str  # UUID du client dans Supabase
    lead_generation_goal: str = "fill_pipeline"  # ou "find_hiring_companies", "local_businesses"
    target_count: int = 500  # Nombre de leads souhaités
    regions: Optional[List[str]] = None  # Override regions (default: from ClientContext)
```

**Output Schema**:
```python
class LeadGenCoordinatorOutputSchema(BaseIOSchema):
    strategy: str  # "google_maps_only", "jobspy_only", "hybrid"

    google_maps_searches: List[GoogleMapsSearchParams]
    # [
    #   {
    #     "query": "agence marketing",
    #     "cities": ["Paris", "Lyon", "Marseille"],
    #     "max_results_per_city": 50
    #   },
    #   {
    #     "query": "agence SaaS",
    #     "cities": ["Paris", "Lyon"],
    #     "max_results_per_city": 30
    #   }
    # ]

    jobspy_searches: List[JobSpySearchParams]
    # [
    #   {
    #     "job_title": "Head of Sales",
    #     "location": "France",
    #     "company_size": ["51-200", "201-500"]
    #   },
    #   {
    #     "job_title": "VP Marketing",
    #     "location": "Ile-de-France",
    #     "company_size": ["11-50", "51-200"]
    #   }
    # ]

    linkedin_searches: List[LinkedInSearchParams]  # Future

    estimated_total_leads: int
    reasoning: str  # Why this strategy was chosen
```

**Logique de l'agent**:
```python
def analyze_client_context(client_context: ClientContext) -> Strategy:
    """
    Analyse le contexte client et détermine la stratégie.

    Exemples:
    - Client = Kaleads (lead gen B2B)
      → ICP: SaaS, Tech, Consulting
      → Stratégie: Google Maps + JobSpy
      → Keywords: "agence marketing", "agence SaaS", "consulting"
      → JobSpy: "Head of Sales", "VP Marketing" (hiring = need leads)

    - Client = Restaurant Local Service
      → ICP: Restaurants, Hôtels, Commerces locaux
      → Stratégie: Google Maps only
      → Keywords: "restaurant", "hôtel", "boulangerie"
      → Villes: Toutes les villes de France/Belgique

    - Client = HR Tech (recrutement)
      → ICP: Entreprises qui recrutent
      → Stratégie: JobSpy primary + Google Maps
      → JobSpy: Tous les postes par industrie ciblée
      → Google Maps: "agence de recrutement", "cabinet RH"
    """

    pain_type = classify_pain_type(client_context.pain_solved)

    if pain_type == "lead_generation":
        # Focus sur les entreprises qui ont besoin de leads
        return hybrid_strategy(
            google_maps_keywords=["agence marketing", "agence SaaS", "consulting"],
            jobspy_keywords=["Head of Sales", "VP Marketing", "Business Developer"]
        )

    elif pain_type == "local_services":
        # Focus sur les commerces locaux
        return google_maps_only_strategy(
            keywords=["restaurant", "hôtel", "commerce"],
            all_cities=True
        )

    elif pain_type == "hr_recruitment":
        # Focus sur les entreprises qui recrutent
        return jobspy_primary_strategy(
            job_titles=extract_relevant_job_titles(client_context.target_industries),
            company_sizes=["11-50", "51-200", "201-500"]
        )
```

### 1.2. Système de Classification Automatique

**Pain Type Detection**:
```python
def classify_pain_type(pain_solved: str) -> str:
    """
    Classifie le type de problème résolu par le client.

    Returns:
        - "lead_generation": Client aide à générer des leads
        - "local_services": Client cible les commerces locaux
        - "hr_recruitment": Client aide au recrutement
        - "devops_infrastructure": Client vend DevOps/infrastructure
        - "marketing_automation": Client vend marketing automation
        - "generic": Autre
    """
    pain_lower = pain_solved.lower()

    # Lead generation
    if any(kw in pain_lower for kw in ["lead", "prospect", "acquisition client", "pipeline"]):
        return "lead_generation"

    # Local services
    if any(kw in pain_lower for kw in ["restaurant", "hôtel", "local", "commerce", "livraison"]):
        return "local_services"

    # HR/Recruitment
    if any(kw in pain_lower for kw in ["recrutement", "rh", "talent", "hiring"]):
        return "hr_recruitment"

    # DevOps/Infrastructure
    if any(kw in pain_lower for kw in ["devops", "infrastructure", "déploiement", "cloud"]):
        return "devops_infrastructure"

    # Marketing automation
    if any(kw in pain_lower for kw in ["marketing", "automation", "email", "campagne"]):
        return "marketing_automation"

    return "generic"
```

**Keyword Generation par ICP**:
```python
def generate_google_maps_keywords(
    target_industries: List[str],
    pain_type: str
) -> List[str]:
    """
    Génère les mots-clés Google Maps en fonction de l'ICP.

    Exemples:
    - ICP: ["SaaS", "Tech"] + pain_type: "lead_generation"
      → ["agence marketing digital", "agence SaaS", "consulting B2B"]

    - ICP: ["Restaurants", "Hôtels"] + pain_type: "local_services"
      → ["restaurant", "hôtel", "café", "boulangerie"]

    - ICP: ["Tech", "Startups"] + pain_type: "hr_recruitment"
      → ["startup", "scale-up", "entreprise tech"]
    """

    # Mapping par industrie
    industry_keywords = {
        "SaaS": ["agence SaaS", "éditeur de logiciel", "startup SaaS"],
        "Tech": ["agence web", "startup tech", "scale-up technologique"],
        "Consulting": ["cabinet de conseil", "consulting", "conseil stratégique"],
        "E-commerce": ["boutique en ligne", "e-commerce", "site marchand"],
        "Marketing": ["agence marketing", "agence digitale", "agence communication"],
        "Restaurant": ["restaurant", "bistrot", "brasserie"],
        "Hôtellerie": ["hôtel", "résidence hôtelière"],
        "Retail": ["boutique", "magasin", "commerce de détail"]
    }

    keywords = []
    for industry in target_industries:
        if industry in industry_keywords:
            keywords.extend(industry_keywords[industry])

    # Fallback si aucune industrie reconnue
    if not keywords:
        keywords = ["entreprise", "société", "startup"]

    return list(set(keywords))  # Remove duplicates


def generate_jobspy_searches(
    target_industries: List[str],
    pain_type: str
) -> List[JobSpySearchParams]:
    """
    Génère les recherches JobSpy en fonction de l'ICP.

    Logique:
    - Pour "lead_generation": Chercher des postes Sales/Marketing (= besoin de leads)
    - Pour "hr_recruitment": Chercher tous les postes (= entreprises qui recrutent)
    - Pour "devops_infrastructure": Chercher des postes DevOps/SRE (= besoin d'infra)
    """

    if pain_type == "lead_generation":
        # Entreprises qui recrutent en Sales/Marketing = besoin de leads
        return [
            JobSpySearchParams(
                job_title="Head of Sales",
                location="France",
                company_size=["11-50", "51-200"]
            ),
            JobSpySearchParams(
                job_title="VP Marketing",
                location="France",
                company_size=["11-50", "51-200"]
            ),
            JobSpySearchParams(
                job_title="Business Developer",
                location="France",
                company_size=["11-50", "51-200"]
            )
        ]

    elif pain_type == "hr_recruitment":
        # Toutes les entreprises qui recrutent
        return [
            JobSpySearchParams(
                job_title="",  # All jobs
                location="France",
                company_size=["11-50", "51-200", "201-500"],
                industries=target_industries
            )
        ]

    elif pain_type == "devops_infrastructure":
        # Entreprises qui recrutent DevOps = besoin d'infra
        return [
            JobSpySearchParams(
                job_title="DevOps Engineer",
                location="France",
                company_size=["11-50", "51-200"]
            ),
            JobSpySearchParams(
                job_title="SRE",
                location="France",
                company_size=["11-50", "51-200"]
            )
        ]

    return []
```

---

## Phase 2: API Endpoints

### 2.1. Endpoint Principal: Coordinator Analyze

**Route**: `POST /api/v2/coordinator/analyze`

**Request**:
```json
{
  "client_id": "kaleads",
  "lead_generation_goal": "fill_pipeline",
  "target_count": 500,
  "regions": ["France", "Belgique"]  // Optional
}
```

**Response**:
```json
{
  "success": true,
  "strategy": "hybrid",
  "reasoning": "Client Kaleads targets B2B SaaS companies. Best strategy: Google Maps for agencies + JobSpy for hiring signals (Sales/Marketing roles).",

  "google_maps_searches": [
    {
      "query": "agence marketing digital",
      "cities": ["Paris", "Lyon", "Marseille", "Toulouse", "Bordeaux"],
      "max_results_per_city": 50,
      "estimated_results": 250
    },
    {
      "query": "agence SaaS",
      "cities": ["Paris", "Lyon", "Nantes"],
      "max_results_per_city": 30,
      "estimated_results": 90
    }
  ],

  "jobspy_searches": [
    {
      "job_title": "Head of Sales",
      "location": "France",
      "company_size": ["11-50", "51-200"],
      "estimated_results": 80
    },
    {
      "job_title": "VP Marketing",
      "location": "France",
      "company_size": ["11-50", "51-200"],
      "estimated_results": 60
    }
  ],

  "estimated_total_leads": 480,
  "execution_plan": {
    "step_1": "Run Google Maps searches (estimated time: 10 min)",
    "step_2": "Run JobSpy searches (estimated time: 5 min)",
    "step_3": "Deduplicate and enrich (estimated time: 2 min)",
    "total_estimated_time_minutes": 17
  }
}
```

### 2.2. Endpoint Google Maps Search

**Route**: `POST /api/v2/leads/google-maps`

**Request**:
```json
{
  "query": "agence marketing digital",
  "cities": ["Paris", "Lyon"],
  "max_results_per_city": 50,
  "api_key": "your-rapidapi-key"  // Optional, from .env by default
}
```

**Response**:
```json
{
  "success": true,
  "results": [
    {
      "name": "Agence XYZ",
      "address": "123 rue de Paris, 75001 Paris",
      "phone": "+33 1 23 45 67 89",
      "website": "https://agence-xyz.fr",
      "rating": 4.5,
      "reviews_count": 234,
      "place_id": "ChIJ...",
      "city": "Paris"
    },
    ...
  ],
  "total_found": 87,
  "cities_searched": ["Paris", "Lyon"]
}
```

### 2.3. Endpoint JobSpy Search

**Route**: `POST /api/v2/leads/jobspy`

**Request**:
```json
{
  "job_title": "Head of Sales",
  "location": "France",
  "company_size": ["11-50", "51-200"],
  "max_results": 100
}
```

**Response**:
```json
{
  "success": true,
  "jobs": [
    {
      "company_name": "Aircall",
      "job_title": "Head of Sales France",
      "location": "Paris",
      "company_size": "51-200",
      "company_website": "https://aircall.io",
      "job_posted_date": "2025-01-10",
      "job_url": "https://...",
      "extracted_signal": "recruiting for sales = need leads"
    },
    ...
  ],
  "total_found": 78,
  "unique_companies": 65
}
```

---

## Phase 3: Intégration avec Scrapers Existants

### 3.1. Google Maps Scraper Integration

**Fichier**: `src/integrations/google_maps_integration.py`

```python
"""
Integration avec Google Maps Scraper (RapidAPI)
"""

import os
from typing import List, Dict
from google_maps_scraper.gmaps_api import GoogleMapsAPI

class GoogleMapsLeadGenerator:
    """
    Wrapper pour générer des leads depuis Google Maps.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("RAPIDAPI_KEY")
        self.client = GoogleMapsAPI(api_key=self.api_key)

    def search_multiple_cities(
        self,
        query: str,
        cities: List[str],
        max_results_per_city: int = 50
    ) -> List[Dict]:
        """
        Recherche le même mot-clé dans plusieurs villes.

        Args:
            query: "agence marketing"
            cities: ["Paris", "Lyon", "Marseille"]
            max_results_per_city: 50

        Returns:
            Liste de leads avec company_name, address, phone, website, etc.
        """
        all_results = []

        for city in cities:
            # Format: "agence marketing Paris France"
            location = f"{city} France"

            results = self.client.search_places(
                query=query,
                location=location,
                page=1,
                language="fr"
            )

            if results and "data" in results:
                # Limiter aux X premiers résultats
                city_results = results["data"][:max_results_per_city]

                # Enrichir avec la ville
                for result in city_results:
                    result["city"] = city
                    result["search_query"] = query

                all_results.extend(city_results)

        return all_results
```

### 3.2. JobSpy Integration

**Fichier**: `src/integrations/jobspy_integration.py`

```python
"""
Integration avec JobSpy API
"""

import requests
from typing import List, Dict, Optional

class JobSpyLeadGenerator:
    """
    Wrapper pour générer des leads depuis JobSpy (offres d'emploi).
    """

    def __init__(self, jobspy_api_url: str = "http://localhost:8000"):
        self.api_url = jobspy_api_url

    def search_jobs(
        self,
        job_title: str,
        location: str,
        company_size: List[str] = None,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Cherche des offres d'emploi et extrait les entreprises.

        Args:
            job_title: "Head of Sales"
            location: "France"
            company_size: ["11-50", "51-200"]
            max_results: 100

        Returns:
            Liste de leads avec company_name, job_title, location, etc.
        """

        # Call JobSpy API
        response = requests.post(
            f"{self.api_url}/api/workflows/execute",
            json={
                "workflow_name": f"search_{job_title}_{location}",
                "search_terms": [job_title],
                "locations": [location],
                "max_results": max_results
            }
        )

        if response.status_code == 200:
            jobs = response.json().get("results", [])

            # Extract unique companies
            companies = {}
            for job in jobs:
                company_name = job.get("company_name")
                if company_name and company_name not in companies:
                    companies[company_name] = {
                        "company_name": company_name,
                        "job_title": job.get("job_title"),
                        "location": job.get("location"),
                        "company_website": job.get("company_url"),
                        "hiring_signal": f"Recruiting for {job.get('job_title')}",
                        "job_posted_date": job.get("date_posted"),
                        "source": "JobSpy"
                    }

            return list(companies.values())

        return []
```

---

## Phase 4: Workflow n8n

### 4.1. Workflow Principal

```
┌────────────────────┐
│ Manual Trigger     │
│ Input: client_id   │
└─────────┬──────────┘
          │
          ↓
┌────────────────────┐
│ HTTP Request       │
│ POST /coordinator/ │
│      analyze       │
│ Get strategy       │
└─────────┬──────────┘
          │
          ↓
┌────────────────────┐
│ Split: Strategy    │
│ ├─ google_maps     │
│ ├─ jobspy          │
│ └─ linkedin        │
└─────────┬──────────┘
          │
     ┌────┴────┐
     │         │
     ↓         ↓
┌─────────┐ ┌─────────┐
│ Loop    │ │ Loop    │
│ GMaps   │ │ JobSpy  │
│ Searches│ │ Searches│
└────┬────┘ └────┬────┘
     │           │
     └─────┬─────┘
           ↓
   ┌───────────────┐
   │ Merge Results │
   │ Deduplicate   │
   └───────┬───────┘
           ↓
   ┌───────────────┐
   │ Enrich Data   │
   │ (Scraping)    │
   └───────┬───────┘
           ↓
   ┌───────────────┐
   │ Write to      │
   │ Google Sheets │
   └───────────────┘
```

### 4.2. Node Configuration Examples

**Node 1: Get Strategy**
```json
{
  "name": "Get Lead Generation Strategy",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "POST",
    "url": "http://kaleads-api-v3:20001/api/v2/coordinator/analyze",
    "authentication": "headerAuth",
    "sendBody": true,
    "bodyParameters": {
      "client_id": "={{ $json.client_id }}",
      "target_count": 500,
      "regions": ["France", "Belgique"]
    }
  }
}
```

**Node 2: Loop Google Maps**
```json
{
  "name": "Loop Google Maps Searches",
  "type": "n8n-nodes-base.splitInBatches",
  "parameters": {
    "batchSize": 1,
    "options": {
      "reset": false
    }
  },
  "inputJson": "={{ $json.google_maps_searches }}"
}
```

**Node 3: Execute Google Maps Search**
```json
{
  "name": "Execute Google Maps Search",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "POST",
    "url": "http://kaleads-api-v3:20001/api/v2/leads/google-maps",
    "sendBody": true,
    "bodyParameters": {
      "query": "={{ $json.query }}",
      "cities": "={{ $json.cities }}",
      "max_results_per_city": "={{ $json.max_results_per_city }}"
    }
  }
}
```

---

## Phase 5: Database Schema (Supabase)

### 5.1. Table: lead_generation_campaigns

```sql
CREATE TABLE lead_generation_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES client_contexts(id),
    campaign_name TEXT NOT NULL,
    strategy TEXT,  -- "google_maps", "jobspy", "hybrid"
    status TEXT DEFAULT 'pending',  -- pending, running, completed, failed
    target_count INT,
    actual_count INT DEFAULT 0,
    google_maps_searches JSONB,
    jobspy_searches JSONB,
    linkedin_searches JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    results_url TEXT  -- URL vers Google Sheets
);
```

### 5.2. Table: leads

```sql
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES lead_generation_campaigns(id),
    company_name TEXT NOT NULL,
    website TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    city TEXT,
    country TEXT DEFAULT 'France',
    industry TEXT,
    company_size TEXT,
    source TEXT,  -- "google_maps", "jobspy", "linkedin"
    source_metadata JSONB,  -- { "search_query": "...", "rating": 4.5, etc. }
    hiring_signal TEXT,  -- Pour JobSpy: "Recruiting for Head of Sales"
    created_at TIMESTAMP DEFAULT NOW(),
    enriched BOOLEAN DEFAULT FALSE,
    enriched_at TIMESTAMP,
    UNIQUE(company_name, city)  -- Avoid duplicates
);
```

---

## Phase 6: Cities Database

### 6.1. Liste des villes (France + Belgique)

**Fichier**: `data/cities_france_belgium.json`

```json
{
  "france": {
    "top_50": [
      "Paris", "Marseille", "Lyon", "Toulouse", "Nice",
      "Nantes", "Montpellier", "Strasbourg", "Bordeaux", "Lille",
      "Rennes", "Reims", "Saint-Étienne", "Toulon", "Le Havre",
      "Grenoble", "Dijon", "Angers", "Nîmes", "Villeurbanne",
      "Saint-Denis", "Le Mans", "Aix-en-Provence", "Clermont-Ferrand", "Brest",
      ...
    ],
    "regions": {
      "Île-de-France": ["Paris", "Boulogne-Billancourt", "Versailles", ...],
      "Auvergne-Rhône-Alpes": ["Lyon", "Grenoble", "Villeurbanne", ...],
      ...
    }
  },
  "belgium": {
    "top_20": [
      "Bruxelles", "Anvers", "Gand", "Charleroi", "Liège",
      "Bruges", "Namur", "Louvain", "Mons", "Malines",
      ...
    ]
  }
}
```

### 6.2. Endpoint pour lister les villes

**Route**: `GET /api/v2/cities`

```json
{
  "countries": ["France", "Belgique"],
  "total_cities": 150,
  "cities": {
    "France": {
      "top_50": [...],
      "by_region": {...}
    },
    "Belgique": {
      "top_20": [...]
    }
  }
}
```

---

## Phase 7: Testing & Validation

### 7.1. Test Scenario 1: Kaleads (Lead Gen B2B)

**Input**:
```json
{
  "client_id": "kaleads",
  "target_count": 500
}
```

**Expected Output**:
```json
{
  "strategy": "hybrid",
  "google_maps_searches": [
    {"query": "agence marketing digital", "cities": ["Paris", "Lyon", "Marseille"]},
    {"query": "agence SaaS", "cities": ["Paris", "Lyon"]},
    {"query": "cabinet de conseil", "cities": ["Paris", "Lyon", "Toulouse"]}
  ],
  "jobspy_searches": [
    {"job_title": "Head of Sales", "location": "France"},
    {"job_title": "VP Marketing", "location": "France"}
  ],
  "estimated_total_leads": 480
}
```

### 7.2. Test Scenario 2: Restaurant Service

**Input**:
```json
{
  "client_id": "local-restaurant-service",
  "target_count": 1000
}
```

**Expected Output**:
```json
{
  "strategy": "google_maps_only",
  "google_maps_searches": [
    {"query": "restaurant", "cities": ["Paris", "Lyon", "Marseille", ...]},
    {"query": "hôtel", "cities": ["Paris", "Lyon", "Marseille", ...]},
    {"query": "café", "cities": ["Paris", "Lyon", "Marseille", ...]}
  ],
  "jobspy_searches": [],
  "estimated_total_leads": 1200
}
```

---

## Phase 8: Roadmap

### MVP (Week 1-2)
- [x] LeadGenCoordinator Agent (analysis logic)
- [x] `/api/v2/coordinator/analyze` endpoint
- [x] Google Maps integration
- [x] JobSpy integration
- [x] Cities database (France top 50)
- [x] Basic n8n workflow

### v1.1 (Week 3)
- [ ] Deduplication logic (company_name + city)
- [ ] Enrichment (scrape company websites for email/phone)
- [ ] LinkedIn integration (via Phantombuster or similar)
- [ ] Belgium cities support
- [ ] Campaign tracking in Supabase

### v1.2 (Week 4)
- [ ] Auto-scheduling (cron jobs in n8n)
- [ ] Webhooks for completed campaigns
- [ ] Export to multiple formats (CSV, Google Sheets, Airtable)
- [ ] Advanced filters (company size, rating, reviews count)

### v2.0 (Month 2)
- [ ] ML-based keyword optimization
- [ ] Lead scoring (based on website content, hiring signals, etc.)
- [ ] Integration with CRM (HubSpot, Salesforce)
- [ ] Multi-language support (EN, ES, DE)

---

## Résumé

### Ce que ça fait
1. **Analyse intelligente**: Le coordinateur lit le contexte client et détermine automatiquement la meilleure stratégie
2. **Génération de recherches**: Crée les mots-clés et paramètres optimaux pour Google Maps et JobSpy
3. **Exécution parallèle**: n8n lance toutes les recherches en parallèle
4. **Agrégation**: Fusionne tous les résultats, déduplique, enrichit
5. **Export**: Remplit automatiquement une Google Sheet avec tous les leads

### Ce que tu fais
1. Appuyer sur "Run" dans n8n
2. Choisir le client_id
3. Récupérer 500+ leads qualifiés dans une Google Sheet en 15 minutes

### Ce que tu ne fais PAS
❌ Réfléchir aux mots-clés manuellement
❌ Faire des recherches une par une
❌ Dupliquer les données
❌ Copier-coller dans des sheets

**Tout est automatisé et adapté au contexte client!** 🚀
