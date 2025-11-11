"""
Agent 4: SignalGeneratorAgent

Objectif: Générer 4 signaux/ciblages ultra-personnalisés (2 signaux d'intention + 2 ciblages).
LE PLUS COMPLEXE des 6 agents.
"""

from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from src.schemas.agent_schemas import SignalGeneratorInput, SignalGeneratorOutput
from typing import Optional


class SignalGeneratorAgent(BaseAgent):
    """
    Agent qui génère des signaux d'intention et ciblages personnalisés.

    Génère 4 outputs:
    - specific_signal_1: Signal d'intention haut volume
    - specific_signal_2: Signal d'intention niche
    - specific_target_1: Ciblage spécifique 1
    - specific_target_2: Ciblage spécifique 2

    Utilise une hiérarchie de fallbacks (1-4) pour garantir toujours un résultat.
    """

    def __init__(self, config: BaseAgentConfig):
        # Créer le system prompt avec la structure complète
        system_prompt = SystemPromptGenerator(
            background=[
                "Tu es un expert en prospection B2B et génération de signaux d'intention.",
                "Tu dois TOUJOURS produire un résultat, même si l'information n'est pas parfaite.",
                "Tu as accès aux Context Providers: PCI, Personas, Pain Points.",
                "Les signaux doivent être ULTRA-SPÉCIFIQUES, pas génériques."
            ],
            steps=[
                "1. Analyse le site web, l'industrie, le product_category et le target_persona",
                "2. Consulte les Context Providers pour comprendre le contexte client",
                "3. Génère 2 signaux d'intention:",
                "   - Signal 1: Haut volume (ex: utilise Salesforce, recrute des Sales)",
                "   - Signal 2: Niche/spécifique (ex: participe à un salon, lève des fonds)",
                "4. Génère 2 ciblages spécifiques:",
                "   - Target 1: Ciblage géographique, taille, ou vertical",
                "   - Target 2: Ciblage technologique ou comportemental",
                "5. Applique la hiérarchie de fallbacks si info manquante",
                "6. Documente ton raisonnement complet (chain-of-thought)"
            ],
            output_instructions=[
                "# FORMAT DE SORTIE",
                "- specific_signal_1: Signal d'intention haut volume (max 150 caractères)",
                "- specific_signal_2: Signal d'intention niche (max 150 caractères)",
                "- specific_target_1: Premier ciblage spécifique (max 150 caractères)",
                "- specific_target_2: Deuxième ciblage spécifique (max 150 caractères)",
                "",
                "# HIÉRARCHIE DE FALLBACKS (OBLIGATOIRE)",
                "",
                "## Niveau 1 : Réponse Idéale",
                "- confidence_score = 5",
                "- fallback_level = 1",
                "- Signaux trouvés explicitement depuis:",
                "  - Contenu du site (intégrations, stack tech, clients mentionnés)",
                "  - Context Providers (personas, pain points, ICP)",
                "- Exemples:",
                "  - specific_signal_1: 'utilisent actuellement Salesforce ou HubSpot'",
                "  - specific_signal_2: 'recrutent activement des Sales ou Customer Success'",
                "  - specific_target_1: 'scale-ups SaaS B2B entre 50 et 500 employés'",
                "  - specific_target_2: 'équipes Sales de 10+ personnes avec CRM en place'",
                "",
                "## Niveau 2 : Réponse Contextuelle",
                "- confidence_score = 4",
                "- fallback_level = 2",
                "- Signaux déduits depuis product_category + industry + target_persona",
                "- Exemples:",
                "  - Si product_category='téléphonie cloud' + industry='SaaS':",
                "    - specific_signal_1: 'entreprises avec équipes commerciales distribuées'",
                "    - specific_signal_2: 'croissance rapide nécessitant scalabilité'",
                "",
                "## Niveau 3 : Réponse Standard",
                "- confidence_score = 3",
                "- fallback_level = 3",
                "- Signaux génériques du secteur",
                "- Exemples:",
                "  - specific_signal_1: 'entreprises en croissance dans le secteur [industry]'",
                "  - specific_target_1: 'dirigeants [target_persona] dans [industry]'",
                "",
                "## Niveau 4 : Fallback Générique",
                "- confidence_score = 2",
                "- fallback_level = 4",
                "- Signaux ultra-génériques",
                "- Exemples:",
                "  - specific_signal_1: 'entreprises cherchant à optimiser leurs processus'",
                "  - specific_target_1: 'décideurs dans des entreprises en croissance'",
                "",
                "# RÈGLES STRICTES",
                "1. TOUJOURS retourner les 6 champs (4 signaux + confidence_score + fallback_level + reasoning)",
                "2. Les signaux doivent être FORMULÉS EN MINUSCULES (sauf acronymes)",
                "3. NE PAS commencer par un verbe d'action ('Ciblent', 'Utilisent')",
                "4. Structure CORRECTE:",
                "   - 'utilisent Salesforce' (correct)",
                "   - 'Utilisent Salesforce' (incorrect - majuscule)",
                "5. Les signaux doivent être CONTEXTUELS, pas génériques",
                "6. specific_signal_1 doit être PLUS LARGE que specific_signal_2",
                "7. specific_target_1 et specific_target_2 doivent être COMPLÉMENTAIRES",
                "8. Le reasoning DOIT expliquer:",
                "   - Pourquoi ces signaux ont été choisis",
                "   - Quel niveau de fallback a été utilisé",
                "   - La logique de priorisation (signal 1 vs signal 2)",
                "9. Ne JAMAIS retourner de valeurs vides",
                "",
                "# EXEMPLES BONS vs MAUVAIS",
                "",
                "## BON (Niveau 1):",
                "- specific_signal_1: 'utilisent actuellement Intercom ou Zendesk'",
                "- specific_signal_2: 'ont levé plus de 5M€ récemment'",
                "- specific_target_1: 'scale-ups B2B SaaS avec 50-200 employés'",
                "- specific_target_2: 'équipes Support de 5+ personnes'",
                "",
                "## MAUVAIS (trop générique):",
                "- specific_signal_1: 'Entreprises en croissance' (majuscule + trop vague)",
                "- specific_signal_2: 'Cherchent à améliorer leur efficacité' (trop générique)",
                "- specific_target_1: 'Décideurs B2B' (pas assez spécifique)",
            ]
        )

        # Configuration de l'agent
        config.system_prompt = system_prompt
        config.input_schema = SignalGeneratorInput
        config.output_schema = SignalGeneratorOutput

        super().__init__(config)

    def run(self, input_data: SignalGeneratorInput) -> SignalGeneratorOutput:
        """
        Exécute l'agent pour générer les signaux.

        Args:
            input_data: SignalGeneratorInput avec company_name, website, industry, product_category, target_persona

        Returns:
            SignalGeneratorOutput avec 4 signaux + scores
        """
        return super().run(input_data)
