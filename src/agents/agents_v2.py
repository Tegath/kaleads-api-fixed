"""
Tous les agents spécialisés pour Atomic Agents v2.

Ce fichier contient les 6 agents avec la nouvelle API:
1. PersonaExtractorAgent
2. CompetitorFinderAgent
3. PainPointAgent
4. SignalGeneratorAgent
5. SystemBuilderAgent
6. CaseStudyAgent
"""

from atomic_agents import AtomicAgent, AgentConfig
from atomic_agents.context import ChatHistory, SystemPromptGenerator
from src.schemas.agent_schemas_v2 import (
    PersonaExtractorInputSchema, PersonaExtractorOutputSchema,
    CompetitorFinderInputSchema, CompetitorFinderOutputSchema,
    PainPointInputSchema, PainPointOutputSchema,
    SignalGeneratorInputSchema, SignalGeneratorOutputSchema,
    SystemBuilderInputSchema, SystemBuilderOutputSchema,
    CaseStudyInputSchema, CaseStudyOutputSchema
)
import instructor
import openai
import os


# ============================================
# Agent 1: PersonaExtractorAgent
# ============================================

class PersonaExtractorAgent:
    """Agent qui identifie le persona cible et la catégorie de produit."""

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        client = instructor.from_openai(openai.OpenAI(api_key=api_key))

        system_prompt_generator = SystemPromptGenerator(
            background=[
                "Tu es un expert en analyse de marchés B2B et identification de personas.",
                "Ta mission est d'identifier le persona cible et la catégorie de produit d'une entreprise.",
                "Tu dois TOUJOURS produire un résultat, même si l'information n'est pas parfaite."
            ],
            steps=[
                "1. Analyse le contenu du site web fourni",
                "2. Identifie les personas mentionnés directement",
                "3. Déduis la catégorie de produit",
                "4. Applique la hiérarchie de fallbacks si info manquante",
                "5. Documente ton raisonnement complet"
            ],
            output_instructions=[
                "target_persona: MINUSCULE sauf 'vP', 'cEO'",
                "product_category: MINUSCULE, factuel",
                "INTERDIT: jargon corporate",
                "fallback_level 1-4 selon qualité de l'info"
            ]
        )

        config = AgentConfig(
            client=client,
            model=model,
            history=ChatHistory(),
            system_prompt_generator=system_prompt_generator
        )

        # Use generic type parameters to specify input and output schemas
        self.agent = AtomicAgent[PersonaExtractorInputSchema, PersonaExtractorOutputSchema](config=config)

    def run(self, input_data: PersonaExtractorInputSchema) -> PersonaExtractorOutputSchema:
        return self.agent.run(user_input=input_data)


# ============================================
# Agent 2: CompetitorFinderAgent
# ============================================

class CompetitorFinderAgent:
    """Agent qui identifie le concurrent principal."""

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        client = instructor.from_openai(openai.OpenAI(api_key=api_key))

        system_prompt_generator = SystemPromptGenerator(
            background=[
                "Tu es un expert en analyse concurrentielle B2B.",
                "Tu dois identifier le concurrent le plus pertinent d'une entreprise.",
                "Tu dois TOUJOURS produire un résultat."
            ],
            steps=[
                "1. Analyse le site web et le secteur",
                "2. Identifie les concurrents mentionnés",
                "3. Déduis le concurrent principal selon le product_category",
                "4. Applique la hiérarchie de fallbacks",
                "5. Documente ton raisonnement"
            ],
            output_instructions=[
                "competitor_name: MINUSCULE sauf acronymes",
                "fallback_level 1-4 selon qualité de l'info"
            ]
        )

        config = AgentConfig(
            client=client,
            model=model,
            history=ChatHistory(),
            system_prompt_generator=system_prompt_generator
        )

        self.agent = AtomicAgent[CompetitorFinderInputSchema, CompetitorFinderOutputSchema](config=config)

    def run(self, input_data: CompetitorFinderInputSchema) -> CompetitorFinderOutputSchema:
        return self.agent.run(user_input=input_data)


# ============================================
# Agent 3: PainPointAgent
# ============================================

class PainPointAgent:
    """Agent qui identifie un pain point spécifique et son impact."""

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        client = instructor.from_openai(openai.OpenAI(api_key=api_key))

        system_prompt_generator = SystemPromptGenerator(
            background=[
                "Tu es un expert en discovery B2B et identification de pain points.",
                "Tu dois identifier un pain point CONCRET et son impact MESURABLE.",
                "Tu dois TOUJOURS produire un résultat."
            ],
            steps=[
                "1. Analyse le site web et le secteur",
                "2. Croise avec le target_persona et product_category",
                "3. Identifie un pain point spécifique (pas générique)",
                "4. Formule l'impact de manière mesurable",
                "5. Applique la hiérarchie de fallbacks",
                "6. Documente ton raisonnement"
            ],
            output_instructions=[
                "problem_specific: Concret et spécifique (max 200 chars)",
                "impact_measurable: Chiffré ou mesurable (max 150 chars)",
                "Exemples BONS: 'perdent 3h/jour à saisir manuellement', '30% de leads perdus'",
                "Exemples MAUVAIS: 'manque d\\'efficacité', 'impact sur la productivité'"
            ]
        )

        config = AgentConfig(
            client=client,
            model=model,
            history=ChatHistory(),
            system_prompt_generator=system_prompt_generator
        )

        self.agent = AtomicAgent[PainPointInputSchema, PainPointOutputSchema](config=config)

    def run(self, input_data: PainPointInputSchema) -> PainPointOutputSchema:
        return self.agent.run(user_input=input_data)


# ============================================
# Agent 4: SignalGeneratorAgent
# ============================================

class SignalGeneratorAgent:
    """Agent qui génère 4 signaux ultra-personnalisés (le plus complexe)."""

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        client = instructor.from_openai(openai.OpenAI(api_key=api_key))

        system_prompt_generator = SystemPromptGenerator(
            background=[
                "Tu es un expert en prospection B2B et génération de signaux d'intention.",
                "Tu dois générer 4 signaux ULTRA-SPÉCIFIQUES (2 signaux + 2 ciblages).",
                "Tu dois TOUJOURS produire un résultat."
            ],
            steps=[
                "1. Analyse le site, industry, product_category, target_persona",
                "2. Génère signal_1 (haut volume) et signal_2 (niche)",
                "3. Génère target_1 (géo/taille) et target_2 (tech/comportement)",
                "4. Applique la hiérarchie de fallbacks",
                "5. Documente ton raisonnement"
            ],
            output_instructions=[
                "FORMULÉS EN MINUSCULES (sauf acronymes)",
                "PAS de verbe d'action en début ('utilisent' OK, 'Utilisent' NON)",
                "specific_signal_1: Plus large que signal_2",
                "specific_target_1 et target_2: COMPLÉMENTAIRES",
                "Exemples: 'utilisent Salesforce', 'scale-ups 50-200 employés'"
            ]
        )

        config = AgentConfig(
            client=client,
            model=model,
            history=ChatHistory(),
            system_prompt_generator=system_prompt_generator
        )

        self.agent = AtomicAgent[SignalGeneratorInputSchema, SignalGeneratorOutputSchema](config=config)

    def run(self, input_data: SignalGeneratorInputSchema) -> SignalGeneratorOutputSchema:
        return self.agent.run(user_input=input_data)


# ============================================
# Agent 5: SystemBuilderAgent
# ============================================

class SystemBuilderAgent:
    """Agent qui identifie 3 systèmes/processus de l'entreprise."""

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        client = instructor.from_openai(openai.OpenAI(api_key=api_key))

        system_prompt_generator = SystemPromptGenerator(
            background=[
                "Tu es un expert en analyse de processus métier et systèmes d'entreprise.",
                "Tu dois identifier 3 systèmes COMPLÉMENTAIRES (pas redondants).",
                "Tu dois TOUJOURS produire un résultat."
            ],
            steps=[
                "1. Analyse company_name, target_persona, problem_specific",
                "2. Déduis les systèmes affectés par le pain point",
                "3. Identifie 3 systèmes COMPLÉMENTAIRES",
                "4. Applique la hiérarchie de fallbacks",
                "5. Documente ton raisonnement"
            ],
            output_instructions=[
                "FORMULÉS EN MINUSCULES",
                "Les 3 systèmes doivent être COMPLÉMENTAIRES",
                "Exemples: 'pipeline Sales', 'qualification leads', 'forecasting'",
                "PAS: 'gestion Sales', 'suivi Sales', 'reporting Sales' (trop similaire)"
            ]
        )

        config = AgentConfig(
            client=client,
            model=model,
            history=ChatHistory(),
            system_prompt_generator=system_prompt_generator
        )

        self.agent = AtomicAgent[SystemBuilderInputSchema, SystemBuilderOutputSchema](config=config)

    def run(self, input_data: SystemBuilderInputSchema) -> SystemBuilderOutputSchema:
        return self.agent.run(user_input=input_data)


# ============================================
# Agent 6: CaseStudyAgent
# ============================================

class CaseStudyAgent:
    """Agent qui génère un résultat de case study mesurable."""

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        client = instructor.from_openai(openai.OpenAI(api_key=api_key))

        system_prompt_generator = SystemPromptGenerator(
            background=[
                "Tu es un expert en rédaction de case studies B2B et storytelling ROI.",
                "Tu dois générer un résultat MESURABLE et CRÉDIBLE.",
                "Tu dois TOUJOURS produire un résultat."
            ],
            steps=[
                "1. Analyse company_name, industry, target_persona, problem_specific",
                "2. Identifie un résultat mesurable pertinent",
                "3. Formule avec des métriques concrètes (%, temps, coût)",
                "4. Applique la hiérarchie de fallbacks",
                "5. Documente ton raisonnement"
            ],
            output_instructions=[
                "Le résultat DOIT contenir une MÉTRIQUE CHIFFRÉE",
                "Pourcentage (+40%), Temps (3h/jour), Coût (50K€), Multiplicateur (x2)",
                "CRÉDIBLE (pas +500% ou ROI en 1 semaine)",
                "Formulation EN MINUSCULES",
                "Exemples: '+42% de conversion en 6 mois', '2.8h/jour économisées'"
            ]
        )

        config = AgentConfig(
            client=client,
            model=model,
            history=ChatHistory(),
            system_prompt_generator=system_prompt_generator
        )

        self.agent = AtomicAgent[CaseStudyInputSchema, CaseStudyOutputSchema](config=config)

    def run(self, input_data: CaseStudyInputSchema) -> CaseStudyOutputSchema:
        return self.agent.run(user_input=input_data)
