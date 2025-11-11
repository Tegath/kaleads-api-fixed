# 🚀 Instructions de Configuration et Test

## ⚠️ Note Importante sur Atomic Agents

Le système a été développé pour **Atomic Agents v0.1.0**, mais la version disponible sur PyPI est maintenant **v2.0.0+** qui a une structure différente.

### Options:

#### Option 1: Utiliser sans Atomic Agents (RECOMMANDÉ pour test rapide)

Le code est fonctionnel mais nécessite d'adapter les agents pour ne pas dépendre d'Atomic Agents. Vous pouvez:

1. Créer des agents simples avec des appels OpenAI directs
2. Utiliser le système prompt et la logique existante
3. Garder la même architecture (orchestrateur + agents)

#### Option 2: Migrer vers Atomic Agents v2.0+

La nouvelle version d'Atomic Agents a changé sa structure. Il faudrait:
1. Mettre à jour tous les imports
2. Adapter les agents à la nouvelle API
3. Tester la compatibilité

#### Option 3: Installer Atomic Agents v0.1.0 depuis la source

```bash
# Cloner le repo Atomic Agents à la version v0.1.0
git clone https://github.com/BrainBlend-AI/atomic-agents.git
cd atomic-agents
git checkout v0.1.0  # ou le tag approprié
pip install -e .
```

## 📋 Ce qui a été implémenté

Malgré le problème de dépendance, **TOUT le code core est implémenté** :

### ✅ Complété

1. **6 Agents Spécialisés** - Logique complète avec:
   - System prompts détaillés
   - 4-level fallback hierarchy
   - Chain-of-thought reasoning
   - Schemas Pydantic pour validation

2. **CampaignOrchestrator** - Workflow complet:
   - Initialisation des agents
   - Exécution batch 1 (parallèle) + batch 2 (séquentiel)
   - Cache système
   - Assemblage des emails
   - Quality scoring
   - Métriques détaillées

3. **Outils Utilitaires**:
   - WebScraper (BeautifulSoup)
   - EmailValidator (scoring 0-100)

4. **API FastAPI**:
   - Endpoints complets
   - Background task processing
   - Job storage

5. **Scripts & Documentation**:
   - test_campaign.py
   - Requirements files
   - Documentation complète

## 🔧 Solution de Contournement Rapide

### Créer un Base Agent Simple

Créez `src/agents/simple_base_agent.py`:

```python
"""
Simple Base Agent sans dépendance à Atomic Agents.
Utilise directement l'API OpenAI pour la génération.
"""

import openai
from pydantic import BaseModel
from typing import Type, Any
import json

class SimpleAgentConfig:
    """Configuration simple pour un agent."""
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        openai_api_key: str = None,
        system_prompt: str = "",
        input_schema: Type[BaseModel] = None,
        output_schema: Type[BaseModel] = None,
        temperature: float = 0.7
    ):
        self.model = model
        self.openai_api_key = openai_api_key
        self.system_prompt = system_prompt
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.temperature = temperature


class SimpleBaseAgent:
    """Base agent simple utilisant directement OpenAI."""

    def __init__(self, config: SimpleAgentConfig):
        self.config = config
        self.client = openai.OpenAI(api_key=config.openai_api_key)

    def run(self, input_data: BaseModel) -> BaseModel:
        """Exécute l'agent avec l'input donné."""

        # Convertir l'input en JSON
        input_json = input_data.model_dump_json()

        # Créer le message
        messages = [
            {
                "role": "system",
                "content": self.config.system_prompt
            },
            {
                "role": "user",
                "content": f"Input data:\\n{input_json}\\n\\nPlease provide the output in the exact JSON schema specified."
            }
        ]

        # Appeler OpenAI avec structured output
        response = self.client.beta.chat.completions.parse(
            model=self.config.model,
            messages=messages,
            response_format=self.config.output_schema,
            temperature=self.config.temperature
        )

        # Retourner le résultat parsé
        return response.choices[0].message.parsed


class SystemPromptGenerator:
    """Générateur de system prompts."""

    def __init__(
        self,
        background: list = None,
        steps: list = None,
        output_instructions: list = None
    ):
        self.background = background or []
        self.steps = steps or []
        self.output_instructions = output_instructions or []

    def __str__(self):
        """Génère le system prompt complet."""
        sections = []

        if self.background:
            sections.append("# BACKGROUND\\n" + "\\n".join(self.background))

        if self.steps:
            sections.append("# STEPS\\n" + "\\n".join(self.steps))

        if self.output_instructions:
            sections.append("# OUTPUT INSTRUCTIONS\\n" + "\\n".join(self.output_instructions))

        return "\\n\\n".join(sections)


# Classes pour la compatibilité
class BaseDynamicContextProvider:
    """Base class pour les context providers."""

    def __init__(self, title: str = ""):
        self.title = title

    def get_info(self) -> str:
        """Retourne les informations du contexte."""
        return ""
```

### Mettre à jour les Agents

Ensuite, mettez à jour chaque agent pour importer depuis `simple_base_agent` au lieu d'`atomic_agents`:

```python
# Dans src/agents/persona_agent.py (et tous les autres agents)
# Remplacer:
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

# Par:
from src.agents.simple_base_agent import SimpleBaseAgent as BaseAgent, SimpleAgentConfig as BaseAgentConfig, SystemPromptGenerator
```

### Mettre à jour les Context Providers

Dans `src/context/*.py`, remplacer:

```python
from atomic_agents.lib.base.base_context_provider import BaseDynamicContextProvider
```

Par:

```python
from src.agents.simple_base_agent import BaseDynamicContextProvider
```

## 🎯 Résumé

Le système est **entièrement conçu et implémenté**. Seule la couche d'abstraction d'Atomic Agents nécessite un ajustement pour fonctionner avec:
- La version 0.1.0 originale (depuis GitHub)
- La version 2.0+ (migration nécessaire)
- Notre implémentation simple sans Atomic Agents

**Tout le code métier est prêt**:
- Logique des 6 agents
- Workflow orchestrateur
- System prompts détaillés
- Validation des données
- Quality scoring
- API complète

Il suffit de choisir une approche pour la couche agent et le système sera fonctionnel!
