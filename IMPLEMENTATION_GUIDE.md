# 🛠️ Guide d'Implémentation - Agents Restants

Ce fichier contient les templates pour implémenter rapidement les agents 2-6.

## Structure d'un Agent

Chaque agent suit cette structure:

```python
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from src.schemas.agent_schemas import AgentInput, AgentOutput

class AgentName(BaseAgent):
    def __init__(self, config: BaseAgentConfig):
        system_prompt = SystemPromptGenerator(
            background=[...],
            steps=[...],
            output_instructions=[
                "# FORMAT DE SORTIE",
                "...",
                "# HIÉRARCHIE DE FALLBACKS",
                "## Niveau 1-4 : ...",
                "# CHAIN-OF-THOUGHT OBLIGATOIRE"
            ]
        )

        config.system_prompt = system_prompt
        config.input_schema = AgentInput
        config.output_schema = AgentOutput
        super().__init__(config)
```

## Agent 2: CompetitorFinderAgent

**Fichier**: `src/agents/competitor_agent.py`

**Mission**: Identifier le concurrent principal utilisé par l'entreprise cible

**Inputs**: company_name, website, industry, product_category (from Agent 1)

**Outputs**: competitor_name, competitor_product_category

**Méthodologie**:
1. Scrape site web (page "/customers", "/integrations", "/alternatives")
2. Recherche mentions de concurrents (ex: "migrate from Zendesk", "vs Salesforce")
3. Fallbacks:
   - Niveau 1: Concurrent trouvé sur site
   - Niveau 2: Concurrent depuis Context Provider (competitors.json)
   - Niveau 3: Concurrent déduit de l'industrie + product_category
   - Niveau 4: Concurrent générique du secteur

## Agent 3: PainPointAgent

**Fichier**: `src/agents/pain_agent.py`

**Mission**: Identifier le pain point spécifique que l'entreprise rencontre

**Inputs**: company_name, website, industry, target_persona, product_category

**Outputs**: problem_specific, impact_measurable

**Méthodologie**:
1. Analyse du contexte pain_points fourni
2. Match avec le persona et l'industrie
3. Formulation spécifique à l'entreprise
4. Fallbacks:
   - Niveau 1: Pain point adapté au contexte exact
   - Niveau 2: Pain point de l'industrie
   - Niveau 3: Pain point générique du persona
   - Niveau 4: Pain point universel B2B

## Agent 4: SignalGeneratorAgent (LE PLUS COMPLEXE)

**Fichier**: `src/agents/signal_agent.py`

**Mission**: Générer 4 signaux d'intention ultra-qualifiés

**Inputs**: company_name, website, industry, product_category, target_persona

**Outputs**: specific_signal_1, specific_signal_2, specific_target_1, specific_target_2

**Méthodologie**: SUIVRE EXACTEMENT `good_agent.md`

```python
# Charger good_agent.md dans le system prompt
with open("good_agent.md", "r", encoding="utf-8") as f:
    good_agent_methodology = f.read()

system_prompt = SystemPromptGenerator(
    background=[
        "Tu es un expert en génération de signaux d'intention B2B ultra-qualifiés.",
        "Tu dois IMPÉRATIVEMENT suivre la méthodologie complète de good_agent.md ci-dessous.",
        f"\\n\\n{good_agent_methodology}\\n\\n",
        "Le contexte entreprise (PCI, personas, pain points) est fourni automatiquement."
    ],
    steps=[
        "1. ÉTAPE 1 : Analyse Approfondie du Positionnement (good_agent.md lignes 22-53)",
        "2. ÉTAPE 2 : Analyse Concurrentielle (good_agent.md lignes 56-85)",
        "3. ÉTAPE 3 : Identification Signaux Actionnables (good_agent.md lignes 87-143)",
        "4. ÉTAPE 4 : Croisement et Combinaison (good_agent.md lignes 146-180)",
        "5. ÉTAPE 5 : Validation et Optimisation (good_agent.md lignes 183-218)",
        "6. Applique hiérarchie de fallbacks si signaux trop génériques"
    ],
    output_instructions=[
        "Signal 1 = Volume élevé (500-2000 entreprises)",
        "Signal 2 = Niche (100-500 entreprises)",
        "SANS majuscule au début (minuscule)",
        "SANS verbe d'action ('Cibler', 'Viser')",
        "Maximum 12 mots par signal",
        "Structure : [segment] [avec/utilisant/ayant] [signal 1] et [signal 2]"
    ]
)
```

## Agent 5: SystemBuilderAgent

**Fichier**: `src/agents/system_agent.py`

**Mission**: Identifier 3 systèmes/processes de l'entreprise

**Inputs**: company_name, target_persona, specific_target_1, specific_target_2, problem_specific

**Outputs**: system_1, system_2, system_3

**Méthodologie**:
1. Déduit les systèmes depuis les signaux (specific_target_1/2)
2. Fait le lien avec le problem_specific
3. Format: nom du système/tool (ex: "Salesforce", "Excel", "email")

## Agent 6: CaseStudyAgent

**Fichier**: `src/agents/case_study_agent.py`

**Mission**: Générer un résultat mesurable inspiré des case studies

**Inputs**: company_name, industry, target_persona, problem_specific

**Outputs**: case_study_result

**Méthodologie**:
1. Utilise CaseStudyProvider pour charger les exemples
2. Adapte les métriques au secteur de l'entreprise
3. Format: résultat mesurable crédible

---

## Prochaine Étape: Orchestrateur

Une fois les 6 agents créés, implémenter:

**`src/orchestrator/campaign_orchestrator.py`**

L'orchestrateur:
1. Charge les Context Providers
2. Exécute les agents en parallèle (batch 1: 1,2,3,6)
3. Exécute séquentiellement (batch 2: 4→5)
4. Assemble l'email final
5. Valide la qualité
6. Gère le cache

Voir le fichier `plan_atomic_agents_campagne_email.md` lignes 413-698 pour l'implémentation complète.
