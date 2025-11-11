"""
Agent 3: PainPointAgent

Objectif: Identifier un pain point spécifique et son impact mesurable.
"""

from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from src.schemas.agent_schemas import PainPointInput, PainPointOutput
from typing import Optional


class PainPointAgent(BaseAgent):
    """
    Agent qui identifie un pain point spécifique et son impact mesurable.

    Utilise une hiérarchie de fallbacks (1-4) pour garantir toujours un résultat.
    """

    def __init__(self, config: BaseAgentConfig):
        # Créer le system prompt avec la structure complète
        system_prompt = SystemPromptGenerator(
            background=[
                "Tu es un expert en discovery B2B et identification de pain points.",
                "Tu dois TOUJOURS produire un résultat, même si l'information n'est pas parfaite.",
                "Tu as accès aux Context Providers: PCI, Pain Points, Personas."
            ],
            steps=[
                "1. Analyse le site web et le secteur d'activité",
                "2. Consulte le Context Provider 'Pain Points' pour les pain points connus du client",
                "3. Croise avec le target_persona et product_category",
                "4. Identifie un pain point spécifique (pas générique)",
                "5. Formule l'impact de manière mesurable (temps, coût, risque)",
                "6. Applique la hiérarchie de fallbacks si info manquante",
                "7. Documente ton raisonnement complet (chain-of-thought)"
            ],
            output_instructions=[
                "# FORMAT DE SORTIE",
                "- problem_specific: Pain point concret et spécifique (max 200 caractères)",
                "- impact_measurable: Impact chiffré ou mesurable (max 150 caractères)",
                "",
                "# HIÉRARCHIE DE FALLBACKS (OBLIGATOIRE)",
                "",
                "## Niveau 1 : Réponse Idéale",
                "- confidence_score = 5",
                "- fallback_level = 1",
                "- Pain point trouvé explicitement dans Context Provider 'Pain Points'",
                "- OU pain point déduit du contenu du site (page problèmes, testimonials, case studies)",
                "- Exemple: problem_specific='vos équipes perdent 3h/jour à saisir manuellement les données'",
                "",
                "## Niveau 2 : Réponse Contextuelle",
                "- confidence_score = 4",
                "- fallback_level = 2",
                "- Pain point déduit depuis product_category + target_persona",
                "- Exemple: Si product_category='CRM' et persona='VP Sales' → 'absence de visibilité sur le pipeline'",
                "",
                "## Niveau 3 : Réponse Standard",
                "- confidence_score = 3",
                "- fallback_level = 3",
                "- Pain point générique du secteur",
                "- Exemple: Si industry='SaaS' → 'croissance ralentie par des processus manuels'",
                "",
                "## Niveau 4 : Fallback Générique",
                "- confidence_score = 2",
                "- fallback_level = 4",
                "- Pain point ultra-générique",
                "- Exemple: problem_specific='processus inefficaces', impact_measurable='perte de temps et d\\'argent'",
                "",
                "# RÈGLES STRICTES",
                "1. TOUJOURS retourner les 5 champs (problem_specific, impact_measurable, confidence_score, fallback_level, reasoning)",
                "2. problem_specific DOIT être concret (éviter 'manque de', 'absence de')",
                "3. impact_measurable DOIT contenir un chiffre, une durée, ou un risque quantifiable",
                "4. Exemples BONS:",
                "   - problem_specific: 'vos équipes Sales perdent 15h/semaine à qualifier manuellement les leads'",
                "   - impact_measurable: '30% de leads qualifiés perdus par manque de réactivité'",
                "5. Exemples MAUVAIS:",
                "   - problem_specific: 'manque d\\'efficacité' (trop vague)",
                "   - impact_measurable: 'impact sur la productivité' (pas mesurable)",
                "6. Le reasoning DOIT expliquer quel niveau de fallback a été utilisé",
                "7. Ne JAMAIS retourner de valeurs vides"
            ]
        )

        # Configuration de l'agent
        config.system_prompt = system_prompt
        config.input_schema = PainPointInput
        config.output_schema = PainPointOutput

        super().__init__(config)

    def run(self, input_data: PainPointInput) -> PainPointOutput:
        """
        Exécute l'agent pour identifier le pain point.

        Args:
            input_data: PainPointInput avec company_name, website, industry, target_persona, product_category

        Returns:
            PainPointOutput avec problem_specific, impact_measurable, scores
        """
        return super().run(input_data)
