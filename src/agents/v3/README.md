# v3.0 Agents - Context-Aware + Web-Enhanced

## 🎯 Philosophie v3.0

Les agents v3.0 sont **génériques et réutilisables**. Ils s'adaptent au client via :
1. **ClientContext** : Contexte client standardisé
2. **Tavily** : Recherche web pour données factuelles
3. **Graceful fallback** : Fonctionnent même sans web search

## ✨ Nouveautés v3.0

### 1. ClientContext Standardisé

Tous les agents acceptent un `ClientContext` :

```python
from src.models.client_context import ClientContext
from src.agents.v3 import CompetitorFinderV3

# Charger le contexte client
context = ClientContext(
    client_id="kaleads-uuid",
    client_name="Kaleads",
    competitors=["HubSpot", "Salesforce"]
)

# Passer aux agents
agent = CompetitorFinderV3(client_context=context)
```

**Bénéfices** :
- ✅ Agent évite de suggérer votre client comme concurrent
- ✅ Adapter le comportement selon `pain_solved`, `target_industries`, etc.
- ✅ Utiliser les vraies case studies du client

### 2. Tavily Web Search

Les agents utilisent Tavily pour recherche web **quand pertinent** :

```python
agent = CompetitorFinderV3(enable_tavily=True)

result = agent.run(CompetitorFinderInputSchema(
    company_name="Aircall",
    industry="SaaS"
))

# Si Tavily trouve un concurrent
print(result.competitor_name)  # "Talkdesk"
print(result.source)  # "web_search"
print(result.confidence_score)  # 5/5
```

**Agents qui utilisent Tavily** :
- **CompetitorFinderV3** : `tavily.search_competitors()`
- **SignalDetectorV3** : `tavily.search_company_news()`  (à venir)
- **SystemMapperV3** : `tavily.search_tech_stack()`  (à venir)

### 3. Graceful Fallback

Si Tavily n'est pas configuré, les agents fonctionnent quand même :

```python
# Sans Tavily
agent = CompetitorFinderV3(enable_tavily=False)

result = agent.run(...)

# Fallback sur logique d'inférence
print(result.source)  # "inference"
print(result.confidence_score)  # 3/5
```

## 🚀 Usage

### CompetitorFinderV3

**Stratégie de recherche** (par ordre de priorité) :
1. **Tavily web search** (confidence: 5/5, fallback: 0)
2. **Site scraping** (confidence: 4/5, fallback: 1)
3. **Industry inference** (confidence: 3/5, fallback: 2)
4. **Generic fallback** (confidence: 1/5, fallback: 3)

**Exemple complet** :

```python
from src.models.client_context import ClientContext
from src.providers.supabase_client import SupabaseClient
from src.agents.v3 import CompetitorFinderV3

# 1. Charger le contexte client
supabase = SupabaseClient()
context = supabase.load_client_context_v3("kaleads-uuid")

# 2. Initialiser l'agent
agent = CompetitorFinderV3(
    enable_tavily=True,  # Enable web search
    enable_scraping=True,  # Enable site scraping
    client_context=context  # Pass client context
)

# 3. Exécuter
from src.agents.v3.competitor_finder_v3 import CompetitorFinderInputSchema

result = agent.run(CompetitorFinderInputSchema(
    company_name="Aircall",
    website="https://aircall.io",
    industry="SaaS",
    product_category="cloud phone solution"
))

# 4. Résultats
print(f"Competitor: {result.competitor_name}")
print(f"Category: {result.competitor_product_category}")
print(f"Confidence: {result.confidence_score}/5")
print(f"Fallback level: {result.fallback_level}")
print(f"Source: {result.source}")
print(f"Reasoning: {result.reasoning}")
```

**Output avec Tavily** :
```
Competitor: Talkdesk
Category: cloud phone solution
Confidence: 5/5
Fallback level: 0
Source: web_search
Reasoning: Found via Tavily web search for 'Aircall' competitors
```

**Output sans Tavily** (fallback) :
```
Competitor: RingCentral
Category: cloud phone solution
Confidence: 3/5
Fallback level: 1
Source: inference
Reasoning: Inferred from industry 'SaaS' and product category 'cloud phone solution'
```

## 📊 Comparaison v2 vs v3

| Aspect | v2.x | v3.0 |
|--------|------|------|
| **Context injection** | String/Dict incohérent | `ClientContext` standardisé |
| **Web search** | ❌ Non | ✅ Tavily |
| **Competitor detection** | Devine | Recherche web réelle |
| **Client filtering** | Manual | Automatique via `ClientContext` |
| **Confidence score** | Pas de granularité | 1-5 avec source |
| **Fallback** | Hardcodé | Multi-niveau (web → scrape → inference → generic) |

## 🔧 Configuration

### Variables d'environnement

```bash
# Tavily (recommandé)
TAVILY_API_KEY=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

# Supabase (requis pour ClientContext)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key

# OpenRouter (requis pour agents)
OPENROUTER_API_KEY=sk-or-v1-your-key
```

### Installation

```bash
# Installer Tavily
pip install tavily-python

# Installer les dépendances
pip install -e .
```

## 🧪 Tests

```python
# Test avec mock context
from src.models.client_context import ClientContext, CaseStudy

context = ClientContext(
    client_id="test",
    client_name="TestCorp",
    offerings=["lead generation"],
    competitors=["HubSpot"],
    real_case_studies=[
        CaseStudy(
            company="TestClient",
            industry="SaaS",
            result="augmenter leur pipeline de 200%"
        )
    ]
)

agent = CompetitorFinderV3(
    client_context=context,
    enable_tavily=True
)

result = agent.run(...)
assert result.competitor_name != "HubSpot"  # Client's competitor filtered out
assert result.competitor_name != "TestCorp"  # Client filtered out
```

## 📝 Agents à venir

- [ ] **PainPointAnalyzerV3** : Adapte le type de pain point selon `client_context.pain_solved`
- [ ] **SignalDetectorV3** : Utilise Tavily pour trouver vraies news
- [ ] **SystemMapperV3** : Utilise Tavily pour détecter tech stack
- [ ] **ProofGeneratorV3** : Utilise `client_context.real_case_studies`

## 💡 Bonnes pratiques

1. **Toujours passer ClientContext** :
   ```python
   # ✅ BIEN
   agent = CompetitorFinderV3(client_context=context)

   # ❌ ÉVITER (moins efficace)
   agent = CompetitorFinderV3()
   ```

2. **Activer Tavily en production** :
   ```python
   # ✅ BIEN (web search activée)
   agent = CompetitorFinderV3(enable_tavily=True)

   # ⚠️ OK pour tests seulement
   agent = CompetitorFinderV3(enable_tavily=False)
   ```

3. **Vérifier la confidence_score** :
   ```python
   result = agent.run(...)

   if result.confidence_score >= 4:
       # Haute confiance (web search ou scraping)
       print(f"Found: {result.competitor_name}")
   else:
       # Basse confiance (inference)
       print(f"Inferred: {result.competitor_name}")
   ```

4. **Utiliser fallback_level pour décisions** :
   ```python
   if result.fallback_level == 0:
       # Meilleur résultat possible (Tavily)
       use_in_email = True
   elif result.fallback_level <= 2:
       # Résultat acceptable (inference)
       use_in_email = True
   else:
       # Résultat générique, éviter dans l'email
       use_in_email = False
   ```

## 🔗 Liens

- [ARCHITECTURE_FONDAMENTALE.md](../../../ARCHITECTURE_FONDAMENTALE.md) : Guide conceptuel complet
- [PLAN_ACTION_V3.md](../../../PLAN_ACTION_V3.md) : Plan d'implémentation détaillé
- [IMPLEMENTATION_LOG.md](../../../IMPLEMENTATION_LOG.md) : Log des changements

---

*Version: 3.0.0*
*Dernière mise à jour : 14 novembre 2025*
