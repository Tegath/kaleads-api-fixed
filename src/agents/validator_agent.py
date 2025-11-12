"""
EmailValidatorAgent - Valide la qualité des emails générés

Vérifie:
- Capitalis

ation correcte
- Ponctuation correcte
- 100% français
- Logique correcte (client → prospect)
- Données factuelles (compare avec contenu scrapé)
"""

from typing import Optional, List
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator, ChatHistory
import instructor
import openai
import os


class EmailValidationInputSchema(BaseIOSchema):
    """Input schema for email validation"""
    email_content: str = Field(..., description="Email complet à valider")
    contact_company: str = Field(..., description="Nom de l'entreprise prospectée")
    client_name: str = Field(..., description="Nom du client qui prospecte")
    client_offering: str = Field(..., description="Ce que le client vend")
    scraped_content: str = Field(default="", description="Contenu scrapé du site du prospect")


class EmailValidationOutputSchema(BaseIOSchema):
    """Output schema for email validation"""
    is_valid: bool = Field(..., description="True si l'email est de qualité suffisante (>= 95%)")
    quality_score: int = Field(..., ge=0, le=100, description="Score de qualité 0-100")
    issues: List[str] = Field(default_factory=list, description="Liste des problèmes détectés")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions d'amélioration")


class EmailValidatorAgent:
    """
    Agent de validation d'emails

    Vérifie:
    - Capitalisation (pas de majuscule après {{variable}})
    - Ponctuation (pas de ..)
    - Français 100%
    - Logique (parle du besoin du prospect pour le service du client)
    - Données factuelles
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "openai/gpt-4o-mini"):
        """
        Initialize validator agent

        Args:
            api_key: OpenRouter API key
            model: Model to use (default: gpt-4o-mini for cost efficiency)
        """
        # Setup client
        api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OpenRouter API key required")

        client = instructor.from_openai(
            openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        )

        # Define validation criteria
        background = [
            "You are an email quality validator for B2B prospecting emails.",
            "You check emails for quality issues and provide a score from 0-100.",
            "",
            "VALIDATION CRITERIA:",
            "",
            "1. CAPITALIZATION (20 points):",
            "   - Check for incorrect capitals after template variables",
            "   - Example BAD: 'J'ai vu que {{company}} Vient de lever' (capital V)",
            "   - Example GOOD: 'J'ai vu que {{company}} vient de lever' (lowercase v)",
            "",
            "2. PUNCTUATION (15 points):",
            "   - Check for double punctuation (..)",
            "   - Check for missing spaces after punctuation",
            "",
            "3. FRENCH QUALITY (25 points):",
            "   - Email must be 100% French",
            "   - Deduct 10 points for EACH English word found",
            "   - Common mistakes: 'lead', 'pipeline', 'marketing automation'",
            "",
            "4. LOGIC CORRECTNESS (25 points):",
            "   - Email should talk about prospect's need for MORE CLIENTS/LEADS",
            "   - NOT about prospect's internal problems (unless relevant)",
            "   - Check: Does pain point relate to getting more business?",
            "",
            "5. FACTUAL ACCURACY (15 points):",
            "   - If scraped_content provided, verify facts against it",
            "   - Deduct points for invented data (fake funding, fake hiring, etc.)",
            "   - If no scraped_content, assume facts are OK",
            "",
            "SCORING:",
            "- 95-100: Perfect, ready to send",
            "- 85-94: Good but has minor issues",
            "- 70-84: Acceptable but needs improvement",
            "- 0-69: Poor, must be regenerated",
        ]

        steps = [
            "1. Check capitalization after variables (look for patterns like '}} X' where X is uppercase)",
            "2. Check for double punctuation ('..')",
            "3. Check for English words (scan entire email)",
            "4. Check logic: does email talk about prospect needing MORE CLIENTS?",
            "5. If scraped_content provided, verify factual claims",
            "6. Calculate quality_score based on issues found",
            "7. Set is_valid = True if score >= 95",
            "8. List all issues found",
            "9. Provide suggestions for improvement",
        ]

        output_instructions = [
            "Return JSON with is_valid, quality_score, issues, suggestions.",
            "Be strict: deduct points for each issue found.",
            "issues should be specific: 'Incorrect capital after company name: Vient → vient'",
            "suggestions should be actionable: 'Change Vient to vient on line 3'",
        ]

        system_prompt_generator = SystemPromptGenerator(
            background=background,
            steps=steps,
            output_instructions=output_instructions,
        )

        config = AgentConfig(
            client=client,
            model=model,
            history=ChatHistory(),
            system_prompt_generator=system_prompt_generator,
        )

        self.agent = AtomicAgent[EmailValidationInputSchema, EmailValidationOutputSchema](config=config)

    def run(self, input_data: EmailValidationInputSchema) -> EmailValidationOutputSchema:
        """
        Validate an email

        Args:
            input_data: Email validation input

        Returns:
            EmailValidationOutputSchema with is_valid, quality_score, issues, suggestions
        """
        return self.agent.run(user_input=input_data)
