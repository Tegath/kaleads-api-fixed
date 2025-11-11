"""
Agent 5: SystemBuilderAgent

Objectif: Identifier 3 systèmes/processus spécifiques à l'entreprise cible.
Dépend des outputs d'Agent 1 (persona), Agent 3 (pain), Agent 4 (targets).
"""

from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from src.schemas.agent_schemas import SystemBuilderInput, SystemBuilderOutput
from typing import Optional


class SystemBuilderAgent(BaseAgent):
    """
    Agent qui identifie 3 systèmes/processus spécifiques à l'entreprise.

    Utilise les outputs des agents précédents pour contextualiser les systèmes.
    Utilise une hiérarchie de fallbacks (1-4) pour garantir toujours un résultat.
    """

    def __init__(self, config: BaseAgentConfig):
        # Créer le system prompt avec la structure complète
        system_prompt = SystemPromptGenerator(
            background=[
                "Tu es un expert en analyse de processus métier et systèmes d'entreprise.",
                "Tu dois TOUJOURS produire un résultat, même si l'information n'est pas parfaite.",
                "Tu as accès aux Context Providers: PCI, Personas, Pain Points.",
                "Les systèmes doivent être CONCRETS et SPÉCIFIQUES à l'entreprise."
            ],
            steps=[
                "1. Analyse le company_name, target_persona, et problem_specific",
                "2. Déduis les systèmes/processus affectés par le pain point",
                "3. Utilise specific_target_1 et specific_target_2 pour contextualiser",
                "4. Identifie 3 systèmes COMPLÉMENTAIRES:",
                "   - system_1: Système principal (ex: 'CRM', 'pipeline Sales')",
                "   - system_2: Système secondaire (ex: 'qualification leads', 'onboarding clients')",
                "   - system_3: Système tertiaire (ex: 'reporting', 'forecasting')",
                "5. Applique la hiérarchie de fallbacks si info manquante",
                "6. Documente ton raisonnement complet (chain-of-thought)"
            ],
            output_instructions=[
                "# FORMAT DE SORTIE",
                "- system_1: Premier système/processus (max 100 caractères)",
                "- system_2: Deuxième système/processus (max 100 caractères)",
                "- system_3: Troisième système/processus (max 100 caractères)",
                "",
                "# HIÉRARCHIE DE FALLBACKS (OBLIGATOIRE)",
                "",
                "## Niveau 1 : Réponse Idéale",
                "- confidence_score = 5",
                "- fallback_level = 1",
                "- Systèmes déduits depuis:",
                "  - problem_specific (ex: si pain='perte de 3h/jour à saisir données' → system_1='CRM')",
                "  - specific_target_1 et specific_target_2 (contexte entreprise)",
                "  - target_persona (ex: si 'VP Sales' → systèmes liés aux Sales)",
                "- Exemples:",
                "  - system_1: 'pipeline de vente et suivi des opportunités'",
                "  - system_2: 'qualification et scoring des leads entrants'",
                "  - system_3: 'reporting hebdomadaire et prévisions de chiffre'",
                "",
                "## Niveau 2 : Réponse Contextuelle",
                "- confidence_score = 4",
                "- fallback_level = 2",
                "- Systèmes déduits depuis target_persona uniquement",
                "- Exemples:",
                "  - Si target_persona='VP Sales':",
                "    - system_1: 'gestion du pipeline commercial'",
                "    - system_2: 'suivi des performances Sales'",
                "    - system_3: 'prévisions de revenus'",
                "",
                "## Niveau 3 : Réponse Standard",
                "- confidence_score = 3",
                "- fallback_level = 3",
                "- Systèmes génériques du secteur",
                "- Exemples:",
                "  - system_1: 'gestion de la relation client'",
                "  - system_2: 'suivi des leads et prospects'",
                "  - system_3: 'reporting et analytics'",
                "",
                "## Niveau 4 : Fallback Générique",
                "- confidence_score = 2",
                "- fallback_level = 4",
                "- Systèmes ultra-génériques",
                "- Exemples:",
                "  - system_1: 'processus commerciaux'",
                "  - system_2: 'gestion opérationnelle'",
                "  - system_3: 'suivi de performance'",
                "",
                "# RÈGLES STRICTES",
                "1. TOUJOURS retourner les 6 champs (system_1, system_2, system_3, confidence_score, fallback_level, reasoning)",
                "2. Les systèmes doivent être FORMULÉS EN MINUSCULES",
                "3. Les 3 systèmes doivent être COMPLÉMENTAIRES (pas redondants)",
                "4. Structure CORRECTE:",
                "   - 'gestion du pipeline commercial' (correct)",
                "   - 'Gestion du Pipeline Commercial' (incorrect - majuscules)",
                "5. Éviter les redondances:",
                "   - BON: system_1='pipeline Sales', system_2='qualification leads', system_3='forecasting'",
                "   - MAUVAIS: system_1='gestion Sales', system_2='suivi Sales', system_3='reporting Sales' (trop similaire)",
                "6. Les systèmes doivent être ACTIONNABLES et CONCRETS",
                "7. Le reasoning DOIT expliquer:",
                "   - Pourquoi ces 3 systèmes ont été choisis",
                "   - Le lien avec le problem_specific",
                "   - Quel niveau de fallback a été utilisé",
                "8. Ne JAMAIS retourner de valeurs vides",
                "",
                "# EXEMPLES BONS vs MAUVAIS",
                "",
                "## BON (Niveau 1):",
                "- system_1: 'pipeline de vente et suivi des opportunités'",
                "- system_2: 'processus de qualification et scoring automatique'",
                "- system_3: 'reporting hebdomadaire des performances commerciales'",
                "Reasoning: 'Déduit depuis problem_specific (perte de temps en saisie manuelle) → systèmes liés à la productivité Sales'",
                "",
                "## MAUVAIS (redondant + majuscules):",
                "- system_1: 'Gestion des Ventes' (majuscules incorrectes)",
                "- system_2: 'Suivi des Ventes' (redondant avec system_1)",
                "- system_3: 'Reporting des Ventes' (pas assez différencié)",
            ]
        )

        # Configuration de l'agent
        config.system_prompt = system_prompt
        config.input_schema = SystemBuilderInput
        config.output_schema = SystemBuilderOutput

        super().__init__(config)

    def run(self, input_data: SystemBuilderInput) -> SystemBuilderOutput:
        """
        Exécute l'agent pour identifier les systèmes.

        Args:
            input_data: SystemBuilderInput avec company_name, target_persona, specific_target_1/2, problem_specific

        Returns:
            SystemBuilderOutput avec system_1, system_2, system_3, scores
        """
        return super().run(input_data)
