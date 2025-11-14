# 🚀 v3.0 Quick Start Guide

Quick reference for using the v3.0 agents.

---

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your keys:
# - OPENROUTER_API_KEY
# - TAVILY_API_KEY
# - SUPABASE_URL
# - SUPABASE_KEY
```

---

## 🎯 Basic Usage

### 1. Load Client Context

```python
from src.providers.supabase_client import SupabaseClient

# Load client context from Supabase
supabase = SupabaseClient()
client_context = supabase.load_client_context_v3("kaleads-uuid")

print(client_context.client_name)  # "Kaleads"
print(client_context.pain_solved)   # "génération de leads B2B..."
print(client_context.offerings)     # ["Cold email automation", ...]
```

### 2. Use Individual Agents

#### PersonaExtractorV3
```python
from src.agents.v3 import PersonaExtractorV3
from src.agents.v3.persona_extractor_v3 import PersonaExtractorInputSchema

# Initialize with client context
agent = PersonaExtractorV3(
    enable_scraping=True,
    enable_tavily=True,
    client_context=client_context
)

# Run
result = agent.run(PersonaExtractorInputSchema(
    company_name="Aircall",
    website="https://aircall.io",
    industry="SaaS"
))

print(result.role)                  # "Head of Sales"
print(result.department)            # "Sales"
print(result.seniority_level)       # "VP / Director"
print(result.likely_pain_points)    # ["Difficulté à générer leads...", ...]
print(result.confidence_score)      # 3
print(result.source)                # "inference"
```

#### CompetitorFinderV3
```python
from src.agents.v3 import CompetitorFinderV3
from src.agents.v3.competitor_finder_v3 import CompetitorFinderInputSchema

agent = CompetitorFinderV3(
    enable_tavily=True,
    client_context=client_context
)

result = agent.run(CompetitorFinderInputSchema(
    company_name="Aircall",
    website="https://aircall.io",
    industry="SaaS",
    product_category="cloud phone solution"
))

print(result.competitor_name)        # "RingCentral" (from Tavily)
print(result.confidence_score)       # 5 (web search)
print(result.source)                 # "web_search"
```

#### PainPointAnalyzerV3
```python
from src.agents.v3 import PainPointAnalyzerV3
from src.agents.v3.pain_point_analyzer_v3 import PainPointAnalyzerInputSchema

agent = PainPointAnalyzerV3(
    enable_scraping=True,
    enable_tavily=True,
    client_context=client_context
)

result = agent.run(PainPointAnalyzerInputSchema(
    company_name="Aircall",
    website="https://aircall.io",
    industry="SaaS"
))

print(result.pain_point_description)  # "Difficulté à générer suffisamment de leads qualifiés"
print(result.pain_type)               # "client_acquisition" (auto-detected!)
print(result.relevance_to_client)     # "Ce pain point est au cœur de l'offre de Kaleads"
```

#### SignalDetectorV3
```python
from src.agents.v3 import SignalDetectorV3
from src.agents.v3.signal_detector_v3 import SignalDetectorInputSchema

agent = SignalDetectorV3(
    enable_tavily=True,
    client_context=client_context
)

result = agent.run(SignalDetectorInputSchema(
    company_name="Aircall",
    website="https://aircall.io",
    industry="SaaS"
))

print(result.signal_type)             # "hiring"
print(result.signal_description)      # "Aircall recrute actuellement"
print(result.relevance_to_client)     # "Le recrutement indique une phase de croissance → besoin de leads"
print(result.source)                  # "web_search" or "inference"
```

#### SystemMapperV3
```python
from src.agents.v3 import SystemMapperV3
from src.agents.v3.system_mapper_v3 import SystemMapperInputSchema

agent = SystemMapperV3(
    enable_tavily=True,
    client_context=client_context
)

result = agent.run(SystemMapperInputSchema(
    company_name="Aircall",
    website="https://aircall.io",
    industry="SaaS",
    product_category="cloud phone solution"
))

print(result.tech_stack)                 # ["Salesforce", "HubSpot", "Slack", ...]
print(result.relevant_tech)              # ["Salesforce", "HubSpot"] (filtered for CRM/sales)
print(result.integration_opportunities)  # "Intégration native avec Salesforce, HubSpot..."
```

#### ProofGeneratorV3
```python
from src.agents.v3 import ProofGeneratorV3
from src.agents.v3.proof_generator_v3 import ProofGeneratorInputSchema

agent = ProofGeneratorV3(
    enable_scraping=True,
    enable_tavily=True,
    client_context=client_context
)

result = agent.run(ProofGeneratorInputSchema(
    company_name="Aircall",
    website="https://aircall.io",
    industry="SaaS"
))

print(result.proof_statement)   # "Nous avons aidé Aircall à augmenter leur pipeline de 300%"
print(result.proof_type)        # "client_case_studies" or "prospect_achievements"
print(result.confidence_score)  # 5 (if found) or 1 (generic)
```

---

## 🌐 API Usage

### Start API Server

```bash
python src/api/n8n_optimized_api.py
# API runs on http://localhost:8001
```

### Generate Email (curl)

```bash
curl -X POST http://localhost:8001/api/v2/generate-email \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "client_id": "kaleads-uuid",
    "contact": {
      "company_name": "Aircall",
      "first_name": "Sophie",
      "last_name": "Martin",
      "email": "sophie@aircall.io",
      "website": "https://aircall.io",
      "industry": "SaaS"
    },
    "options": {
      "model_preference": "balanced",
      "enable_scraping": true,
      "enable_tavily": true
    }
  }'
```

### Generate Email (Python)

```python
import requests

response = requests.post(
    "http://localhost:8001/api/v2/generate-email",
    headers={
        "Content-Type": "application/json",
        "X-API-Key": "your-api-key"
    },
    json={
        "client_id": "kaleads-uuid",
        "contact": {
            "company_name": "Aircall",
            "first_name": "Sophie",
            "last_name": "Martin",
            "website": "https://aircall.io",
            "industry": "SaaS"
        },
        "options": {
            "enable_scraping": True,
            "enable_tavily": True
        }
    }
)

result = response.json()
print(result["email_content"])
print(result["quality_score"])
print(result["fallback_levels"])
```

---

## 🧪 Testing Different Client Types

### Lead Gen Client (Kaleads)
```python
# Automatically targets: Head of Sales, CMO
# Pain focus: client acquisition, lead generation
# Tech filtering: CRM, sales tools (Salesforce, HubSpot)
client_context = supabase.load_client_context_v3("kaleads-uuid")
```

### HR Tech Client (TalentHub)
```python
# Automatically targets: CHRO, VP HR
# Pain focus: recruitment, talent management
# Tech filtering: HR tools (Workday, Greenhouse, Lever)
# (Assumes you have a TalentHub client in Supabase)
client_context = supabase.load_client_context_v3("talenthub-uuid")
```

### DevOps Client (CloudOps)
```python
# Automatically targets: CTO, VP Engineering
# Pain focus: infrastructure, deployment, scalability
# Tech filtering: Cloud/DevOps tools (AWS, Docker, Kubernetes)
# (Assumes you have a CloudOps client in Supabase)
client_context = supabase.load_client_context_v3("cloudops-uuid")
```

---

## 🎨 Customization

### Disable Tavily (Use Inference Only)
```python
agent = CompetitorFinderV3(
    enable_tavily=False,  # Disable web search
    client_context=client_context
)
# Will use industry inference + generic fallback
```

### Custom Model Selection
```python
from src.providers.openrouter_client import OpenRouterClient

custom_client = OpenRouterClient(
    api_key="your-key",
    model="anthropic/claude-3-sonnet"  # Use premium model
)

agent = PainPointAnalyzerV3(
    api_key="your-key",
    model="anthropic/claude-3-sonnet",
    client_context=client_context
)
```

---

## 📊 Understanding Outputs

### Confidence Score (1-5)
- **5**: Found via web search (Tavily) - HIGH quality
- **4**: Found via website scraping - GOOD quality
- **3**: Inferred from industry/context - OK quality
- **2**: Generic inference - LOW quality
- **1**: Generic fallback - SAFE but generic

### Fallback Level (0-3)
- **0**: Best data source (web search)
- **1**: Good data source (scraping)
- **2**: OK data source (inference)
- **3**: Generic fallback (no specific data found)

### Source
- **"web_search"**: From Tavily API
- **"site_scrape"**: From website content
- **"inference"**: Inferred from industry/context
- **"generic"**: Generic fallback

---

## 🔍 Debugging

### Check Tavily Connection
```python
from src.providers.tavily_client import get_tavily_client

tavily = get_tavily_client()
print(tavily.enabled)  # True if configured

# Test search
results = tavily.search("Aircall competitors")
print(results)
```

### Check Supabase Connection
```python
from src.providers.supabase_client import SupabaseClient

supabase = SupabaseClient()
try:
    context = supabase.load_client_context_v3("test-uuid")
    print("✅ Supabase connected")
except Exception as e:
    print(f"❌ Supabase error: {e}")
```

### Enable Agent Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Agents will print debug messages:
# [CompetitorFinderV3] Using Tavily to find competitors for Aircall
# [CompetitorFinderV3] Tavily found: RingCentral, 8x8, Talkdesk
```

---

## 🚨 Common Issues

### Issue: "Could not initialize Tavily"
**Solution**: Check `TAVILY_API_KEY` in `.env`

### Issue: "Client context not found"
**Solution**: Ensure `client_id` exists in Supabase `clients` table

### Issue: "All agents return fallback_level=3"
**Solution**:
- Enable Tavily with `enable_tavily=True`
- Check Tavily API key is configured
- Verify website is accessible for scraping

### Issue: "Agents returning wrong persona/pain type"
**Solution**: Check `pain_solved` field in ClientContext is descriptive

---

## 📚 Next Steps

1. **Read Documentation**:
   - [ARCHITECTURE_FONDAMENTALE.md](./ARCHITECTURE_FONDAMENTALE.md) - v3 philosophy
   - [src/agents/v3/README.md](./src/agents/v3/README.md) - Detailed agent docs

2. **Run Tests** (when created):
   ```bash
   pytest tests/
   ```

3. **Explore Examples**:
   - See `if __name__ == "__main__"` sections in each agent file
   - Run: `python src/agents/v3/competitor_finder_v3.py`

4. **Customize for Your Client**:
   - Add your client to Supabase
   - Load context with `load_client_context_v3()`
   - Run agents and see automatic adaptation!

---

**Happy Coding! 🚀**
