"""
PersonaExtractorAgent : Identifie le persona cible et la catégorie de produit (Atomic Agents v2).

Cet agent analyse le site web d'une entreprise pour extraire:
- target_persona: Le persona cible (ex: "vP Sales", "cOO")
- product_category: La catégorie de produit/service (ex: "solution de téléphonie cloud")
"""

from atomic_agents import AtomicAgent, AgentConfig
from atomic_agents.context import ChatHistory
from src.schemas.agent_schemas_v2 import PersonaExtractorInputSchema, PersonaExtractorOutputSchema
import instructor
import openai
import os


def create_persona_extractor_agent(
    api_key: str = None,
    model: str = "gpt-4o-mini"
) -> AtomicAgent:
    """
    Crée un PersonaExtractorAgent configuré.

    Args:
        api_key: Clé API OpenAI (ou depuis env OPENAI_API_KEY)
        model: Modèle à utiliser

    Returns:
        AtomicAgent configuré pour extraire le persona
    """

    # System prompt détaillé
    system_prompt = """# ROLE
Tu es un expert en analyse de marchés B2B et identification de personas.
Ta mission est d'identifier le persona cible et la catégorie de produit d'une entreprise.
Tu dois TOUJOURS produire un résultat, même si l'information n'est pas parfaite.

# STEPS
1. Analyse le contenu du site web fourni (priorise homepage, customers, testimonials, about)
2. Identifie les personas mentionnés directement (titres de jobs dans témoignages, cas clients)
3. Déduis la catégorie de produit depuis la description (homepage, meta description)
4. Applique la hiérarchie de fallbacks si info manquante (voir ci-dessous)
5. Documente ton raisonnement complet dans le champ 'reasoning'

# OUTPUT FORMAT
- target_persona: TOUJOURS en MINUSCULE sauf 'vP', 'cEO', 'cOO', etc. (ex: 'vP Sales')
- product_category: TOUJOURS en MINUSCULE, max 6 mots, description factuelle
- INTERDIT: jargon corporate (innovant, leader, disruptif, révolutionnaire, etc.)
- INTERDIT: retourner 'N/A', 'Unknown' ou champ vide

# HIÉRARCHIE DE FALLBACKS (OBLIGATOIRE)

## Niveau 1 : Réponse Idéale (Priorité Maximale)
- Persona trouvé explicitement dans testimonials ou case studies
- Product category déduit de la homepage
- confidence_score = 5
- fallback_level = 1

## Niveau 2 : Réponse Contextuelle (Si Niveau 1 impossible)
- Persona déduit du contenu (ex: page 'customers' → personas clients)
- Product category depuis meta description ou tagline
- confidence_score = 4
- fallback_level = 2

## Niveau 3 : Réponse Standard (Si Niveau 2 impossible)
- Persona basé sur l'industrie (SaaS → 'vP Sales', FinTech → 'cFO')
- Product category générique mais précis (ex: 'logiciel de gestion')
- confidence_score = 3
- fallback_level = 3

## Niveau 4 : Réponse Générique (DERNIER RECOURS)
- Persona générique selon industrie
- Product category très large mais toujours valide
- confidence_score = 2
- fallback_level = 4

# EXEMPLES DE BONNES RÉPONSES

✅ CORRECT:
- target_persona: "vP Sales"
- product_category: "solution de téléphonie cloud"

❌ INCORRECT:
- target_persona: "VP Sales" (majuscule incorrecte)
- product_category: "solution innovante de téléphonie" (jargon)

# CHAIN-OF-THOUGHT OBLIGATOIRE
Dans le champ 'reasoning', documente:
1. Quelles sections du site tu as analysées
2. Quels indices t'ont mené à cette conclusion
3. Pourquoi ce fallback level
4. Niveau de confiance justifié
"""

    # Créer le client OpenAI avec instructor
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    client = instructor.from_openai(openai.OpenAI(api_key=api_key))

    # Créer la configuration de l'agent
    config = AgentConfig(
        client=client,
        model=model,
        history=ChatHistory(),
        system_role=system_prompt
    )

    # Créer et retourner l'agent
    return AtomicAgent(config=config)


class PersonaExtractorAgent:
    """
    Wrapper pour PersonaExtractorAgent compatible avec l'ancienne API.
    """

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        """
        Initialise l'agent.

        Args:
            api_key: Clé API OpenAI
            model: Modèle à utiliser
        """
        self.agent = create_persona_extractor_agent(api_key=api_key, model=model)
        self.api_key = api_key
        self.model = model

    def run(self, input_data: PersonaExtractorInputSchema) -> PersonaExtractorOutputSchema:
        """
        Exécute l'agent pour extraire le persona.

        Args:
            input_data: PersonaExtractorInputSchema avec company_name, website, etc.

        Returns:
            PersonaExtractorOutputSchema avec target_persona, product_category, scores
        """
        # AtomicAgent.run() prend directement l'input schema
        response = self.agent.run(user_input=input_data)

        return response
