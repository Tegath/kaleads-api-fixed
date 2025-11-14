"""
EmailWriter Agent v3.1

Generates final email content following template guidelines and examples.
This agent ensures the email follows formatting rules, tone, and style perfectly.
"""

from atomic_agents.lib.base.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field
from typing import Optional, Dict, Any
import os


class EmailWriterInputSchema(BaseIOSchema):
    """Input for EmailWriter agent."""

    # Template to follow
    template_content: str = Field(
        description="Template with {{variables}} placeholders to fill"
    )

    # Variables to inject
    variables: Dict[str, str] = Field(
        description="Dictionary of variable names and values to replace in template"
    )

    # Guidelines context (from ClientContext)
    email_guidelines_context: str = Field(
        default="",
        description="Formatted guidelines and examples from ClientContext"
    )

    # Client info for context
    client_name: str = Field(
        description="Name of the client sending the email"
    )

    client_offerings: str = Field(
        description="What the client sells/offers"
    )


class EmailWriterOutputSchema(BaseIOSchema):
    """Output from EmailWriter agent."""

    email_content: str = Field(
        description="Final email content with perfect formatting and tone"
    )

    guidelines_followed: bool = Field(
        description="Whether the guidelines were successfully followed"
    )

    tone_match_score: int = Field(
        ge=0, le=100,
        description="How well the tone matches the guidelines (0-100)"
    )

    formatting_corrections: list[str] = Field(
        default_factory=list,
        description="List of formatting corrections that were applied"
    )


class EmailWriterAgent(BaseAgent):
    """
    EmailWriter Agent v3.1

    Generates final email content by:
    1. Taking a template with {{variables}}
    2. Filling variables with provided values
    3. Following email guidelines EXACTLY
    4. Learning from example emails
    5. Ensuring perfect formatting (spacing, punctuation, capitalization)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        model = model or "anthropic/claude-3.5-sonnet"

        system_prompt = """You are an expert email copywriter for cold outreach.

Your job is to generate PERFECTLY formatted cold emails by:
1. Taking a template with {{variable}} placeholders
2. Replacing placeholders with provided variable values
3. Following the email guidelines EXACTLY (tone, style, structure)
4. Learning from the example emails provided
5. Ensuring PERFECT formatting (spacing, punctuation, capitalization)

CRITICAL FORMATTING RULES:
- Single space after all punctuation (periods, commas, question marks, exclamation marks)
- NO double spaces anywhere
- Capitalize the first word after a sentence (after period, question mark, exclamation mark)
- Capitalize after a variable if it starts a new sentence
- Maximum 2 consecutive line breaks (no triple+ line breaks)
- Proper greeting capitalization ("Bonjour" not "bonjour")

TONE MATCHING:
- If guidelines say "conversational", use natural spoken language
- If guidelines say "professional", use proper business tone
- If guidelines say "casual", be friendly and relaxed
- If guidelines say "direct", get to the point quickly

STRUCTURE RULES:
- Follow the template structure
- Don't add extra paragraphs unless guidelines say to
- Keep CTAs (calls-to-action) clear and single
- Match the length specified in guidelines

EXAMPLE LEARNING:
- Study the perfect examples provided
- Notice their tone, structure, word choice
- Mimic what makes them work
- Don't copy verbatim, but learn the patterns

You will receive:
- template_content: Template with {{variables}}
- variables: Dict of variable_name → value
- email_guidelines_context: Formatted guidelines + examples
- client_name: Who's sending the email
- client_offerings: What they sell

Return:
- email_content: PERFECTLY formatted email
- guidelines_followed: true/false
- tone_match_score: 0-100
- formatting_corrections: List of fixes you applied

IMPORTANT: Focus on quality over speed. Every email should be perfect."""

        config = BaseAgentConfig(
            client=self._get_client(api_key),
            model=model,
            system_prompt_template=system_prompt,
            input_schema=EmailWriterInputSchema,
            output_schema=EmailWriterOutputSchema
        )

        super().__init__(config)

    def _get_client(self, api_key: str):
        """Get OpenRouter client for LLM calls."""
        from openai import OpenAI
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )


if __name__ == "__main__":
    """Test EmailWriter agent."""

    print("="*60)
    print("🧪 Testing EmailWriter Agent v3.1")
    print("="*60)

    agent = EmailWriterAgent()

    # Test input
    template = """Bonjour {{first_name}},

J'ai remarqué que {{company_name}} {{specific_signal_1}}, donc ça m'a donné envie de vous contacter.

En tant que {{target_persona}}, vous faites surement face à {{problem_specific}}, non? .

Je demande car on a aidé: {{case_study_result}} à obtenir {{result}} sans avoir {{second_problem}}.
Ce serait pertinent à explorer ou pas du tout ?

Cordialement"""

    variables = {
        "first_name": "Cathy",
        "company_name": "Jumppe",
        "specific_signal_1": "recrute actuellement",
        "target_persona": "Head of Engineering",
        "problem_specific": "difficulté à scaler l'équipe DevOps",
        "case_study_result": "TechCorp",
        "result": "+200% de déploiements/semaine",
        "second_problem": "recruter 10+ DevOps"
    }

    guidelines = """
📧 EMAIL TEMPLATE CONTEXT:
- Intention: Generate a meeting for DevOps outsourcing
- Tone: conversational
- Approach: Signal-focused + Social proof
- Style: Direct and concise (< 120 words)

DO:
  ✅ Use natural, spoken language
  ✅ Keep it under 120 words
  ✅ Ask engaging questions
  ✅ Show value with specific metrics

DON'T:
  ❌ Use corporate jargon
  ❌ Make it too long
  ❌ Have formatting errors (spacing, caps)

📨 EXAMPLE OF PERFECT EMAIL:
For a contact: company_name: Aircall, first_name: Sophie, industry: SaaS

EMAIL:
Bonjour Sophie,

Vu qu'Aircall recrute en ce moment, je me suis dit que vous étiez en croissance.

On aide des boîtes comme vous à scaler sans recruter 10+ DevOps.

On a aidé TechCorp à passer de 20 à 400 déploiements/semaine en 3 mois.

Ça vous parle?

WHY IT WORKS:
- Opens with their signal (hiring)
- Shows empathy for their situation
- Gives specific metric (20 → 400 deploys)
- Natural conversational tone
- Clear CTA
"""

    print("\n1️⃣ Running EmailWriter agent...")
    print(f"   Template has formatting errors: 'non? .' and 'ça' not capitalized")

    result = agent.run(EmailWriterInputSchema(
        template_content=template,
        variables=variables,
        email_guidelines_context=guidelines,
        client_name="DevOps Experts",
        client_offerings="DevOps partagé, part-time DevOps"
    ))

    print("\n2️⃣ Results:")
    print("="*60)
    print("GENERATED EMAIL:")
    print("="*60)
    print(result.email_content)
    print("="*60)

    print(f"\n📊 Quality Metrics:")
    print(f"   - Guidelines followed: {'✅' if result.guidelines_followed else '❌'}")
    print(f"   - Tone match score: {result.tone_match_score}/100")

    if result.formatting_corrections:
        print(f"\n🔧 Formatting corrections applied:")
        for i, correction in enumerate(result.formatting_corrections, 1):
            print(f"   {i}. {correction}")
    else:
        print(f"\n✨ No formatting corrections needed")

    print("\n" + "="*60)
    print("✅ EmailWriter test complete!")
    print("="*60)
