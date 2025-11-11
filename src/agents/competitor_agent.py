"""
Agent 2: CompetitorFinderAgent

Objectif: Identifier le concurrent le plus pertinent pour le prospect.
"""

from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from src.schemas.agent_schemas import CompetitorFinderInput, CompetitorFinderOutput
from typing import Optional


class CompetitorFinderAgent(BaseAgent):
    """
    Agent qui identifie le concurrent le plus pertinent d'une entreprise.

    Utilise une hiérarchie de fallbacks (1-4) pour garantir toujours un résultat.
    """

    def __init__(self, config: BaseAgentConfig):
        # Créer le system prompt avec la structure complète
        system_prompt = SystemPromptGenerator(
            background=[
                "Tu es un expert en analyse concurrentielle B2B et veille stratégique.",
                "Tu dois TOUJOURS produire un résultat, même si l'information n'est pas parfaite.",
                "Tu as accès aux Context Providers: PCI, Competitors, Case Studies."
            ],
            steps=[
                "1. Analyse le contenu du site web et le secteur d'activité",
                "2. Consulte le Context Provider 'Competitors' pour les concurrents connus",
                "3. Identifie les outils/solutions mentionnés (intégrations, alternatives, comparaisons)",
                "4. Déduis le concurrent le plus pertinent selon le produit du prospect",
                "5. Applique la hiérarchie de fallbacks si info manquante",
                "6. Documente ton raisonnement complet (chain-of-thought)"
            ],
            output_instructions=[
                "# FORMAT DE SORTIE",
                "- competitor_name: TOUJOURS en MINUSCULE sauf acronymes (ex: 'salesforce', 'hubSpot')",
                "- competitor_product_category: Description précise du produit concurrent",
                "",
                "# HIÉRARCHIE DE FALLBACKS (OBLIGATOIRE)",
                "",
                "## Niveau 1 : Réponse Idéale",
                "- confidence_score = 5",
                "- fallback_level = 1",
                "- Concurrent trouvé explicitement sur le site (page intégrations, comparaisons, 'alternatives to X')",
                "- Ou concurrent trouvé dans Context Provider 'Competitors'",
                "",
                "## Niveau 2 : Réponse Contextuelle",
                "- confidence_score = 4",
                "- fallback_level = 2",
                "- Concurrent déduit depuis product_category et industry",
                "- Exemple: Si product_category='solution de téléphonie cloud' et industry='SaaS' → competitor_name='ringcentral'",
                "",
                "## Niveau 3 : Réponse Standard",
                "- confidence_score = 3",
                "- fallback_level = 3",
                "- Concurrent générique du secteur",
                "- Exemple: Si industry='CRM' → competitor_name='salesforce'",
                "",
                "## Niveau 4 : Fallback Générique",
                "- confidence_score = 2",
                "- fallback_level = 4",
                "- Concurrent ultra-générique",
                "- Exemple: competitor_name='solution legacy', competitor_product_category='outils traditionnels'",
                "",
                "# RÈGLES STRICTES",
                "1. TOUJOURS retourner les 5 champs (competitor_name, competitor_product_category, confidence_score, fallback_level, reasoning)",
                "2. Minuscules pour les noms de concurrents sauf acronymes",
                "3. Le reasoning DOIT expliquer quel niveau de fallback a été utilisé",
                "4. Si plusieurs concurrents trouvés, choisis le plus pertinent selon product_category",
                "5. Ne JAMAIS retourner de valeurs vides"
            ]
        )

        # Configuration de l'agent
        config.system_prompt = system_prompt
        config.input_schema = CompetitorFinderInput
        config.output_schema = CompetitorFinderOutput

        super().__init__(config)

    def run(self, input_data: CompetitorFinderInput) -> CompetitorFinderOutput:
        """
        Exécute l'agent pour identifier le concurrent.

        Args:
            input_data: CompetitorFinderInput avec company_name, website, industry, product_category

        Returns:
            CompetitorFinderOutput avec competitor_name, competitor_product_category, scores
        """
        return super().run(input_data)
