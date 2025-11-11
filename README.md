# 🚀 Kaleads Atomic Agents - Email Campaign Generator

Système multi-agents basé sur Atomic Agents pour générer des campagnes d'emails ultra-personnalisés à partir de contexte client (PCI, personas, pain points).

## 📋 Vue d'Ensemble

Ce projet implémente un système de 6 agents spécialisés coordonnés par un orchestrateur pour générer automatiquement des emails personnalisés de haute qualité.

### Architecture

```
Orchestrator (CampaignOrchestrator)
    ↓
├── Agent 1: PersonaExtractorAgent → target_persona, product_category
├── Agent 2: CompetitorFinderAgent → competitor_name
├── Agent 3: PainPointAgent → problem_specific, impact_measurable
├── Agent 4: SignalGeneratorAgent → specific_signal_1/2, specific_target_1/2
├── Agent 5: SystemBuilderAgent → system_1/2/3
└── Agent 6: CaseStudyAgent → case_study_result
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone le projet
cd kaleads-atomic-agents

# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer dépendances
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copier .env.example vers .env
cp .env.example .env

# Éditer .env avec vos clés API
nano .env
```

Variables requises:
- `OPENAI_API_KEY`: Clé API OpenAI
- `SUPABASE_URL`: URL de votre projet Supabase
- `SUPABASE_KEY`: Clé anon de Supabase
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key pour bypass RLS

### 3. Setup Supabase

```bash
# 1. Créer un projet sur https://supabase.com

# 2. Exécuter le schema SQL
# Copier le contenu de sql/schema.sql
# Coller dans Supabase > SQL Editor > New Query
# Exécuter

# 3. Créer les buckets Storage
# - clients (public)
# - templates (public)
# - exports (private)
```

### 4. Lancer l'API

```bash
# Démarrer le serveur FastAPI
uvicorn src.api.main:app --reload --port 8000

# API disponible sur http://localhost:8000
# Documentation: http://localhost:8000/docs
```

### 5. Test Rapide

```bash
# Uploader des contacts test
python scripts/upload_contacts.py data/test_contacts.csv \
  --client "Test Client" \
  --template "Cold Email V1"

# Générer des emails via l'API
curl -X POST http://localhost:8000/campaigns/generate \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d @examples/campaign_request.json
```

## 📁 Structure du Projet

```
kaleads-atomic-agents/
├── src/
│   ├── agents/              # 6 agents spécialisés
│   │   ├── persona_agent.py
│   │   ├── competitor_agent.py
│   │   ├── pain_agent.py
│   │   ├── signal_agent.py
│   │   ├── system_agent.py
│   │   └── case_study_agent.py
│   ├── context/             # Context Providers
│   │   ├── pci_provider.py
│   │   ├── persona_provider.py
│   │   ├── pain_provider.py
│   │   ├── competitor_provider.py
│   │   └── case_study_provider.py
│   ├── orchestrator/        # Orchestrateur principal
│   │   └── campaign_orchestrator.py
│   ├── api/                 # API FastAPI
│   │   ├── main.py
│   │   └── routes.py
│   ├── schemas/             # Schemas Pydantic
│   │   ├── agent_schemas.py
│   │   └── campaign_schemas.py
│   └── tools/               # Outils (scraping, validation)
│       ├── web_scraper.py
│       └── validator.py
├── scripts/                 # Scripts utilitaires
│   ├── upload_contacts.py   # Upload CSV → Supabase
│   └── migrate_airtable.py  # Migration depuis Airtable
├── data/                    # Données contextuelles
│   ├── clients/             # Dossiers par client
│   └── templates/           # Templates d'emails
├── sql/                     # Schemas SQL
│   └── schema.sql           # Schema PostgreSQL complet
├── n8n/                     # Workflows n8n
│   ├── campaign_generation.json
│   └── export_to_smartlead.json
├── review-interface/        # Interface de review (React)
│   ├── src/
│   ├── package.json
│   └── README.md
├── tests/                   # Tests
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md
```

## 🎯 Utilisation

### Génération de Campagne

```python
from src.orchestrator import CampaignOrchestrator
from src.schemas import CampaignRequest, Contact

# Préparer la requête
request = CampaignRequest(
    template_content="Bonjour {{first_name}} - quand les {{target_persona}} de {{company_name}}...",
    contacts=[
        Contact(
            company_name="Aircall",
            first_name="Sophie",
            website="https://aircall.io",
            industry="SaaS"
        )
    ],
    context={
        "pci": "...",  # Contenu du PCI
        "personas": "...",  # Contenu personas
        "pain_points": "..."  # Contenu pain points
    }
)

# Lancer la génération
orchestrator = CampaignOrchestrator()
result = orchestrator.run(request)

# Résultats
print(f"✅ {result.success_count}/{result.total_contacts} emails générés")
print(f"📊 Score moyen: {result.average_quality_score}/100")
print(f"⚡ Temps: {result.total_execution_time_seconds}s")
print(f"💰 Cache hit rate: {result.cache_hit_rate*100}%")
```

### Via l'API

```bash
# Endpoint principal
POST /campaigns/generate

# Body
{
  "template_content": "...",
  "contacts": [...],
  "context": {...},
  "enable_cache": true
}

# Response
{
  "batch_id": "uuid",
  "emails_generated": [...],
  "success_rate": 0.96,
  "average_quality_score": 87.5,
  ...
}
```

## 📊 Métriques & Monitoring

- **Quality Score**: 0-100 calculé automatiquement
- **Fallback Levels**: Tracking du niveau de fallback par variable
- **Cache Hit Rate**: Optimisation des coûts
- **Execution Time**: Performance monitoring
- **Token Usage**: Tracking des coûts OpenAI

## 🔧 Configuration Avancée

### Activer le Cache

```python
orchestrator = CampaignOrchestrator(enable_cache=True)
```

Le cache stocke les résultats par `company_name` pour réutilisation.

### Ajuster les Modèles

Dans `.env`:
```
OPENAI_MODEL=gpt-4o  # ou gpt-4o-mini pour réduire les coûts
```

### Fallback Hierarchy

Chaque agent implémente 4 niveaux de fallback :
1. **Niveau 1 (Idéal)**: Info trouvée sur le site
2. **Niveau 2 (Contextuel)**: Déduit du contexte client
3. **Niveau 3 (Standard)**: Basé sur l'industrie
4. **Niveau 4 (Générique)**: Fallback universel

## 🚀 Déploiement

### Docker

```bash
# Build
docker build -t kaleads-atomic-agents .

# Run
docker run -p 8000:8000 --env-file .env kaleads-atomic-agents
```

### Railway

```bash
# Push to GitHub
git push origin main

# Sur Railway:
# 1. New Project → Deploy from GitHub
# 2. Sélectionner le repo
# 3. Ajouter les variables d'environnement
# 4. Deploy
```

## 📖 Documentation Complète

- [Guide des Agents](docs/agents.md)
- [Context Providers](docs/context-providers.md)
- [API Reference](docs/api.md)
- [Workflows n8n](docs/n8n.md)
- [Interface de Review](review-interface/README.md)

## 🤝 Contribution

Ce projet suit le plan d'implémentation détaillé dans `plan_atomic_agents_campagne_email.md`.

## 📝 License

Propriétaire - Kaleads 2025
