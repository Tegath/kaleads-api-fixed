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

    # NEW: Optional instructions and example
    email_instructions: str = Field(default="", description="Instructions sur le ton/style à suivre (optionnel)")
    example_email: str = Field(default="", description="Exemple parfait à imiter (optionnel)")


class EmailValidationOutputSchema(BaseIOSchema):
    """Output schema for email validation"""
    is_valid: bool = Field(..., description="True si l'email est de qualité suffisante (>= 95%)")
    quality_score: int = Field(..., ge=0, le=100, description="Score de qualité 0-100")
    issues: List[str] = Field(default_factory=list, description="Liste des problèmes détectés")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions d'amélioration")
    corrected_email: str = Field(..., description="Email avec toutes les corrections appliquées (espaces, majuscules, ponctuation)")


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
            "VALIDATION CRITERIA (Total: 100 points):",
            "",
            "1. CAPITALIZATION (15 points):",
            "   - Check for incorrect capitals after template variables",
            "   - Example BAD: 'J'ai vu que {{company}} Vient de lever' (capital V)",
            "   - Example GOOD: 'J'ai vu que {{company}} vient de lever' (lowercase v)",
            "   - Deduct 15 points if capitalization errors found",
            "",
            "2. PUNCTUATION (10 points):",
            "   - Check for double punctuation (..)",
            "   - Check for missing spaces after punctuation",
            "   - Deduct 10 points if punctuation errors found",
            "",
            "3. FRENCH QUALITY (25 points):",
            "   - Email must be 100% French",
            "   - Deduct 10 points for EACH English word found",
            "   - Common mistakes: 'lead', 'leads', 'pipeline', 'automation'",
            "",
            "4. LOGIC CORRECTNESS (25 points):",
            "   - Email MUST talk about prospect's need for MORE CLIENTS/LEADS/PROSPECTS",
            "   - NEVER about:",
            "     * Internal HR problems (unless client sells HR solutions)",
            "     * Internal tech problems (unless client sells tech solutions)",
            "     * Internal operational problems (unless client sells ops solutions)",
            "   - The pain point must relate to BUSINESS GROWTH, CLIENT ACQUISITION, SALES",
            "   - Deduct 25 points if email talks about wrong type of problem",
            "",
            "5. FACTUAL ACCURACY (25 points) - UPGRADED FROM 15:",
            "   - If scraped_content provided, verify ALL factual claims",
            "   - Deduct 20 points for EACH invented fact:",
            "     * Fake funding amounts ('vient de lever 2M€' not in scraped_content)",
            "     * Fake hiring numbers ('recrute 10 commerciaux' not in scraped_content)",
            "     * Fake product launches (not mentioned in scraped_content)",
            "     * Fake geographic expansions (not mentioned in scraped_content)",
            "   - Check for suspicious patterns:",
            "     * Specific numbers without context",
            "     * Specific locations not mentioned on website",
            "     * Specific timeframes not mentioned on website",
            "   - If scraped_content is empty, cannot verify (assume OK but note uncertainty)",
            "",
            "HALLUCINATION DETECTION:",
            "Look for these red flags in the email:",
            "- 'vient de lever [amount]€' → check if mentioned in scraped_content",
            "- 'recrute [number] personnes' → check if mentioned in scraped_content",
            "- 'vient d'ouvrir à [ville]' → check if mentioned in scraped_content",
            "- Any specific metric or number → verify against scraped_content",
            "",
            "SCORING:",
            "- 95-100: Perfect, ready to send",
            "- 85-94: Good but has minor issues",
            "- 70-84: Acceptable but needs improvement",
            "- 0-69: Poor, must be regenerated (likely hallucinations)",
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
            "Return JSON with is_valid, quality_score, issues, suggestions, AND corrected_email.",
            "Be strict: deduct points for each issue found.",
            "issues should be specific: 'Incorrect capital after company name: Vient → vient'",
            "suggestions should be actionable: 'Change Vient to vient on line 3'",
            "",
            "CRITICAL - AUTO-CORRECTION:",
            "In corrected_email field, return the email with ALL formatting fixes applied:",
            "- Fix all spacing errors (add missing spaces after punctuation, remove double spaces)",
            "- Fix all capitalization errors (lowercase after variables mid-sentence)",
            "- Fix all punctuation errors (remove double punctuation)",
            "- Keep the content and meaning identical, ONLY fix formatting",
            "",
            "IF email_instructions or example_email are provided in the input:",
            "- Use email_instructions to guide the tone/style of corrections",
            "- Use example_email as reference for the desired tone/style",
            "- Make sure corrected_email follows the instructions and matches the example's tone",
            "",
            "Example:",
            "Input: 'J'ai vu que {{company}} Recrute en ce moment, non? . Ça'",
            "corrected_email: 'J'ai vu que {{company}} recrute en ce moment, non?  Ça'",
            "                  (fixed: capital R → r, removed space before period, fixed 'ça' → 'Ça')",
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
