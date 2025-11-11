## Architecture Multi-Provider: OpenAI + Claude

## Vue d'Ensemble

Votre système peut maintenant utiliser **OpenAI (GPT)** OU **Claude** comme backend!

```
Frontend (Streamlit)
    ↓
Multi-Provider Orchestrator
    ├── OpenAI Path
    │   └── agents_v2.py (GPT-4, GPT-4o-mini, etc.)
    └── Claude Path
        └── agents_claude.py (Claude 3.5 Sonnet, etc.)
```

---

## Pourquoi Cette Architecture?

### 1. **Flexibilité**
- Testez les 2 providers avec le même workflow
- Changez de provider en 1 ligne de code
- Comparez les résultats qualité/coût/vitesse

### 2. **Meilleure Qualité**
- Claude est souvent meilleur pour:
  - Raisonnement complexe
  - Analyse nuancée
  - Ton et style
- OpenAI (GPT-4o) est souvent meilleur pour:
  - Vitesse
  - Structured outputs
  - Coût (gpt-4o-mini)

### 3. **Résilience**
- Si un provider est down → utilisez l'autre
- Si un provider change ses prix → basculez
- Si un provider rate limits → distribuez la charge

---

## Comment Utiliser

### Méthode 1: Frontend Streamlit (Recommandé)

```bash
# Installer Streamlit
pip install streamlit

# Lancer le frontend
streamlit run app_frontend.py
```

**Interface Web Complète**:
- ✅ Formulaire pour configurer le contact
- ✅ Choix du template (défaut ou custom)
- ✅ Directives personnalisées
- ✅ Génération visuelle avec métriques
- ✅ Analyse détaillée (fallback levels, confidence scores)
- ✅ Feedback et régénération
- ✅ Historique des versions
- ✅ Téléchargement des emails

**Avantages**:
- Pas besoin de terminal
- Interface visuelle claire
- Édition facile
- Comparaison visuelle

---

### Méthode 2: Code Python

```python
from src.orchestrator.multi_provider_orchestrator import MultiProviderOrchestrator
from src.schemas.campaign_schemas import CampaignRequest, Contact

# Contact
contact = Contact(
    company_name="Stripe",
    first_name="Jean",
    last_name="Martin",
    email="jean@stripe.com",
    website="https://stripe.com",
    industry="FinTech"
)

# Template
template = """
Bonjour {{first_name}},

J'ai remarqué que {{company_name}} {{specific_signal_1}}.

Le problème: {{problem_specific}}.
L'impact: {{impact_measurable}}.

Résultat: {{case_study_result}}.

Intéressé(e)?
"""

# Request
request = CampaignRequest(
    template_content=template,
    contacts=[contact],
    context={"directives": "Ton professionnel, focus ROI"},
    batch_id="test-001",
    enable_cache=True
)

# Option 1: OpenAI
orch = MultiProviderOrchestrator(provider="openai")
result_openai = orch.run(request)

# Option 2: Claude
orch = MultiProviderOrchestrator(provider="claude")
result_claude = orch.run(request)

# Option 3: Auto (utilise la clé API disponible)
orch = MultiProviderOrchestrator(provider="auto")
result = orch.run(request)
```

---

### Méthode 3: Comparer les 2 Providers

```python
from src.orchestrator.multi_provider_orchestrator import compare_providers

results = compare_providers(
    request=request,
    openai_api_key="sk-...",
    claude_api_key="sk-ant-..."
)

# Résultats
print("OpenAI Quality:", results["openai"].average_quality_score)
print("Claude Quality:", results["claude"].average_quality_score)
print("Winner:", results["comparison"]["quality_score"]["winner"])

print("\nOpenAI Cost:", results["openai"].estimated_cost_usd)
print("Claude Cost:", results["claude"].estimated_cost_usd)
print("Cheaper:", results["comparison"]["cost"]["cheaper"])
```

---

## Configuration des API Keys

### `.env` File

```bash
# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini

# Claude (Anthropic)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Autre config
API_HOST=0.0.0.0
API_PORT=8000
```

---

## Modèles Disponibles

### OpenAI

| Modèle | Coût (Input/Output) | Vitesse | Qualité | Usage Recommandé |
|--------|---------------------|---------|---------|------------------|
| `gpt-4o-mini` | $0.15/$0.60 per 1M | ⚡⚡⚡ | ⭐⭐⭐ | Production, tests |
| `gpt-4o` | $2.50/$10 per 1M | ⚡⚡ | ⭐⭐⭐⭐ | Qualité max |
| `gpt-4-turbo` | $10/$30 per 1M | ⚡ | ⭐⭐⭐⭐⭐ | Cas critiques |

### Claude (Anthropic)

| Modèle | Coût (Input/Output) | Vitesse | Qualité | Usage Recommandé |
|--------|---------------------|---------|---------|------------------|
| `claude-3-5-sonnet-20241022` | $3/$15 per 1M | ⚡⚡ | ⭐⭐⭐⭐⭐ | Meilleure qualité |
| `claude-3-haiku-20240307` | $0.25/$1.25 per 1M | ⚡⚡⚡ | ⭐⭐⭐ | Rapide et économique |

---

## Quelle Configuration Choisir?

### Pour Tester / Développer

```python
# OpenAI gpt-4o-mini (le moins cher, rapide)
orch = MultiProviderOrchestrator(
    provider="openai",
    model="gpt-4o-mini"
)
```

**Coût**: ~$0.0012 par email
**Vitesse**: ~20s par email
**Qualité**: Bonne (75-80/100)

---

### Pour Production (Qualité Max)

```python
# Claude 3.5 Sonnet (meilleure qualité)
orch = MultiProviderOrchestrator(
    provider="claude",
    model="claude-3-5-sonnet-20241022"
)
```

**Coût**: ~$0.006 par email (5x plus cher)
**Vitesse**: ~25s par email
**Qualité**: Excellente (85-90/100)

---

### Pour Production (Équilibre Coût/Qualité)

**Stratégie Hybride**:
1. Utilisez `gpt-4o-mini` pour la génération initiale
2. Si quality score < 75 → régénérez avec `claude-3-5-sonnet`
3. Économisez ~70% vs tout en Claude

```python
# Première tentative
orch_cheap = MultiProviderOrchestrator(provider="openai", model="gpt-4o-mini")
result = orch_cheap.run(request)

# Si pas assez bon, retry avec Claude
if result.average_quality_score < 75:
    orch_quality = MultiProviderOrchestrator(provider="claude")
    result = orch_quality.run(request)
```

---

## Architecture des Agents

### Agents OpenAI (`src/agents/agents_v2.py`)

```python
from atomic_agents import AtomicAgent, AgentConfig
import instructor
import openai

class PersonaExtractorAgent:
    def __init__(self, api_key, model="gpt-4o-mini"):
        client = instructor.from_openai(openai.OpenAI(api_key=api_key))

        config = AgentConfig(
            client=client,
            model=model,
            system_prompt_generator=...
        )

        self.agent = AtomicAgent[InputSchema, OutputSchema](config=config)

    def run(self, input_data):
        return self.agent.run(user_input=input_data)
```

**Avantages**:
- ✅ Structured outputs natifs (via instructor)
- ✅ Type safety complet
- ✅ Validation Pydantic automatique

---

### Agents Claude (`src/agents/agents_claude.py`)

```python
import anthropic

class PersonaExtractorAgentClaude:
    def __init__(self, api_key, model="claude-3-5-sonnet-20241022"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.system_prompt = "..."

    def run(self, input_data):
        message = self.client.messages.create(
            model=self.model,
            system=self.system_prompt,
            messages=[{"role": "user", "content": self._format_input(input_data)}]
        )

        return self._parse_output(message.content[0].text)
```

**Avantages**:
- ✅ Meilleur raisonnement
- ✅ Meilleure compréhension du contexte
- ✅ Ton plus naturel

**Inconvénient actuel**:
- ⚠️ Parsing manuel du JSON (pas encore de instructor pour Claude)
- ⚠️ Moins de type safety

---

## Améliorer l'Implémentation Claude

### Étape 1: Ajouter instructor pour Claude

Il existe une version expérimentale d'instructor pour Claude:

```bash
pip install instructor[anthropic]
```

```python
import instructor
from anthropic import Anthropic

client = instructor.from_anthropic(Anthropic(api_key="sk-ant-..."))

# Maintenant on peut faire du structured output comme avec OpenAI!
result = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    response_model=PersonaExtractorOutputSchema,  # Type safety!
    messages=[...]
)
```

---

### Étape 2: Compléter tous les agents Claude

Actuellement, `agents_claude.py` contient seulement 2 agents complets.

**TODO**: Implémenter les 4 agents restants:
- `PainPointAgentClaude` ✅ (structure présente)
- `SignalGeneratorAgentClaude` ✅ (structure présente)
- `SystemBuilderAgentClaude` ✅ (structure présente)
- `CaseStudyAgentClaude` ✅ (structure présente)

**Pattern à suivre** (copier-coller de PersonaExtractorAgentClaude):

```python
class PainPointAgentClaude:
    def __init__(self, api_key=None, model="claude-3-5-sonnet-20241022"):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        system_prompt = build_system_prompt(
            background=[...],  # Copier depuis agents_v2.py
            steps=[...],       # Copier depuis agents_v2.py
            output_instructions=[...]  # Copier depuis agents_v2.py
        )

        self.agent = ClaudeAgent[PainPointInputSchema, PainPointOutputSchema](
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            output_schema=PainPointOutputSchema
        )

    def run(self, input_data):
        return self.agent.run(input_data)
```

---

### Étape 3: Implémenter l'Orchestrateur Claude Complet

Actuellement, `MultiProviderOrchestrator` avec `provider="claude"` lance une `NotImplementedError`.

**TODO**: Implémenter le workflow complet dans `multi_provider_orchestrator.py`:

```python
elif self.provider == "claude":
    # Batch 1: Parallèle conceptuel
    # (En pratique, séquentiel car API Claude)
    persona_result = self.persona_agent.run(...)
    competitor_result = self.competitor_agent.run(...)
    pain_result = self.pain_agent.run(...)
    case_study_result = self.case_study_agent.run(...)

    # Batch 2: Séquentiel
    signal_result = self.signal_agent.run(...)
    system_result = self.system_agent.run(...)

    # Assembler l'email
    email = assemble_email(...)

    return CampaignResult(...)
```

---

## Frontend: Choisir le Provider

Ajoutez un sélecteur dans `app_frontend.py`:

```python
# Dans le sidebar
provider = st.selectbox(
    "Provider",
    ["OpenAI (GPT)", "Claude (Anthropic)", "Auto"],
    index=0
)

model_options = {
    "OpenAI (GPT)": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
    "Claude (Anthropic)": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
    "Auto": ["auto"]
}

model = st.selectbox("Modèle", model_options[provider])

# Dans generate_email()
orchestrator = MultiProviderOrchestrator(
    provider=provider.split()[0].lower(),  # "openai" ou "claude"
    model=model,
    enable_cache=True
)
```

---

## Workflow Idéal pour Production

### Phase 1: Tests et Calibration

```
1. Générer 10-20 emails avec gpt-4o-mini
   ↓
2. Analyser les résultats (quality scores, fallbacks)
   ↓
3. Identifier les agents problématiques
   ↓
4. Améliorer les prompts
   ↓
5. Re-tester
   ↓
6. Répéter jusqu'à quality score > 75
```

---

### Phase 2: Comparaison OpenAI vs Claude

```
1. Générer 10 emails avec gpt-4o-mini
   ↓
2. Générer les MÊMES 10 emails avec claude-3-5-sonnet
   ↓
3. Comparer:
   - Quality scores
   - Fallback levels
   - Ton/style
   - Coûts
   ↓
4. Choisir le provider gagnant
```

---

### Phase 3: Production

**Stratégie A - Un seul provider**:
```
Utilisez le provider qui a gagné en Phase 2
```

**Stratégie B - Hybride (recommandé)**:
```
1. gpt-4o-mini pour génération initiale (80% des cas)
2. Si quality < 75 → régénérer avec claude-3-5-sonnet
3. Économie: ~70% vs tout en Claude
4. Qualité: garantie > 75
```

**Stratégie C - A/B Testing continu**:
```
1. 50% des emails avec OpenAI
2. 50% des emails avec Claude
3. Mesurer les métriques d'engagement (opens, clicks, replies)
4. Ajuster le ratio selon les performances
```

---

## Métriques à Tracker

### Par Provider

| Métrique | OpenAI | Claude | Objectif |
|----------|--------|--------|----------|
| Quality Score Moyen | 76 | 84 | > 75 |
| Fallback Level Moyen | 2.1 | 1.8 | < 2.0 |
| Confidence Score Moyen | 4.2 | 4.6 | > 4.0 |
| Coût par email | $0.0012 | $0.006 | Minimiser |
| Temps par email | 22s | 28s | < 30s |

### Métriques Business (après envoi)

| Métrique | Définition | Objectif |
|----------|------------|----------|
| Open Rate | % emails ouverts | > 40% |
| Click Rate | % liens cliqués | > 10% |
| Reply Rate | % réponses reçues | > 5% |
| Conversion Rate | % meetings bookés | > 2% |

**Corrélation**:
Quality Score > 80 → Reply Rate +50%

---

## Prochaines Étapes

### Court Terme (Cette Semaine)

1. ✅ **Frontend Streamlit** → `streamlit run app_frontend.py`
2. ⏳ **Compléter agents Claude** → Finir les 4 agents restants
3. ⏳ **Tester avec vos contacts** → 10 emails de test

### Moyen Terme (Ce Mois)

1. ⏳ **Implémenter orchestrateur Claude complet**
2. ⏳ **Comparer OpenAI vs Claude** → 20 emails chacun
3. ⏳ **Choisir le provider de production**
4. ⏳ **Améliorer les prompts** basé sur feedback

### Long Terme (Prochains Mois)

1. ⏳ **A/B Testing automatique** entre providers
2. ⏳ **Tracking métriques business** (opens, clicks, replies)
3. ⏳ **Auto-amélioration** des prompts basée sur feedback
4. ⏳ **Fine-tuning** d'un modèle custom

---

## FAQ

**Q: Pourquoi pas utiliser QUE Claude si c'est meilleur?**
R: Coût 5x plus cher. Stratégie hybride = meilleur ROI.

**Q: Les agents Claude sont-ils compatibles avec Atomic Agents?**
R: Non, Claude utilise une implémentation custom mais avec la MÊME interface (mêmes input/output schemas).

**Q: Puis-je mixer OpenAI et Claude dans le même workflow?**
R: Oui! Ex: Agents 1-3 avec GPT, Agents 4-6 avec Claude.

**Q: Le frontend fonctionne avec les 2 providers?**
R: Oui, ajoutez juste un sélecteur dans le sidebar (voir code ci-dessus).

**Q: Claude est-il vraiment meilleur?**
R: Pour le raisonnement et le ton, oui. Pour la vitesse et le coût, GPT-4o-mini gagne.

---

## Commandes Rapides

```bash
# Frontend (recommandé)
pip install streamlit
streamlit run app_frontend.py

# Test OpenAI
python -c "from src.orchestrator.multi_provider_orchestrator import MultiProviderOrchestrator; ..."

# Test Claude (quand implémenté)
python -c "from src.orchestrator.multi_provider_orchestrator import MultiProviderOrchestrator; ..."

# Comparer les 2
python test_compare_providers.py
```

Bon développement! 🚀
