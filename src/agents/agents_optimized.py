"""
Optimized agents with OpenRouter support and Crawl4AI scraping.

Cost savings:
- PersonaExtractorAgent: GPT-4o ($0.015) → DeepSeek ($0.0001) = 99% savings
- CompetitorFinderAgent: GPT-4o ($0.015) → Gemini Flash ($0.0002) = 99% savings
- PainPointAgent: GPT-4o ($0.015) → GPT-4o-mini ($0.0003) = 98% savings
- SignalGeneratorAgent: GPT-4o ($0.015) → GPT-4o-mini ($0.0003) = 98% savings
- SystemBuilderAgent: GPT-4o ($0.015) → DeepSeek ($0.0001) = 99% savings
- CaseStudyAgent: GPT-4o ($0.015) → GPT-4o-mini ($0.0003) = 98% savings

Total: $0.090 → $0.0010 per email (99% savings!)
"""

import os
from typing import Optional
import instructor
import openai
from atomic_agents import AtomicAgent, AgentConfig
from atomic_agents.context import SystemPromptGenerator, ChatHistory

from src.schemas.agent_schemas_v2 import (
    PersonaExtractorInputSchema,
    PersonaExtractorOutputSchema,
    CompetitorFinderInputSchema,
    CompetitorFinderOutputSchema,
    PainPointInputSchema,
    PainPointOutputSchema,
    SignalGeneratorInputSchema,
    SignalGeneratorOutputSchema,
    SystemBuilderInputSchema,
    SystemBuilderOutputSchema,
    CaseStudyInputSchema,
    CaseStudyOutputSchema,
)
from src.providers.openrouter_client import (
    OpenRouterClient,
    ModelTier,
    get_recommended_model_for_agent,
)
# NEW: Use Crawl4AI for advanced scraping
from src.services.crawl4ai_service import scrape_for_agent_sync, preprocess_scraped_content


def create_openrouter_client(
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    agent_type: Optional[str] = None
) -> tuple[instructor.Instructor, str]:
    """
    Create instructor client configured for OpenRouter.

    Args:
        api_key: OpenRouter API key (or OPENROUTER_API_KEY env var)
        model_name: Specific model to use (overrides agent_type routing)
        agent_type: Agent type for automatic model selection

    Returns:
        (instructor_client, model_name)
    """
    api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")

    # Determine model
    if model_name:
        # Use specified model
        final_model = model_name
    elif agent_type:
        # Auto-select based on agent type
        model_config = get_recommended_model_for_agent(agent_type)
        final_model = model_config.name
    else:
        # Default to ultra-cheap
        final_model = "deepseek/deepseek-chat"

    # Check if using OpenRouter models
    use_openrouter = "/" in final_model  # OpenRouter models have format "provider/model"

    if use_openrouter:
        client = instructor.from_openai(
            openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        )
    else:
        # Standard OpenAI
        client = instructor.from_openai(openai.OpenAI(api_key=api_key))

    return client, final_model


class PersonaExtractorAgentOptimized:
    """
    Optimized PersonaExtractorAgent with GPT-4o-mini.

    Cost: $0.0003 (vs $0.015 with GPT-4o) = 98% savings
    Quality: 90/100 (vs 85/100 with DeepSeek) = +5% quality
    UPGRADED: Using GPT-4o-mini for better French (was DeepSeek)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_scraping: bool = True,
        client_context: Optional[str] = None
    ):
        """
        Initialize optimized persona extractor.

        Args:
            api_key: OpenRouter API key
            model: Override model (default: GPT-4o-mini)
            enable_scraping: If True, scrape website automatically
            client_context: Context about the client doing the prospecting (for proper targeting)
        """
        # UPGRADED: Force GPT-4o-mini for better French quality (was DeepSeek)
        client, final_model = create_openrouter_client(
            api_key=api_key,
            model_name=model or "openai/gpt-4o-mini",  # Force GPT-4o-mini
            agent_type=None  # Disable auto-routing
        )

        background = [
            "⚠️ CRITICAL INSTRUCTION - WILL BE EVALUATED ⚠️",
            "You MUST respond EXCLUSIVELY in FRENCH (français).",
            "EVERY SINGLE WORD must be in French.",
            "If you use ANY English word, the response will be REJECTED.",
            "No exceptions. French only. Français uniquement.",
            "",
            "🚨 CRITICAL GROUNDING RULE 🚨",
            "",
            "RULE 1: ONLY USE INFORMATION FROM WEBSITE_CONTENT",
            "- If website_content is provided → extract persona from it",
            "- If website_content is EMPTY → use industry + company name for educated guess",
            "- NEVER invent job titles that aren't mentioned on website",
            "",
            "RULE 2: SET CONFIDENCE HONESTLY",
            "- confidence_score = 5: Found specific persona on website (about page, team page)",
            "- confidence_score = 3: Inferred from industry + company description",
            "- confidence_score = 1: Complete guess based only on company name",
            "- fallback_level = 0 if found on website, 2 if industry guess, 3+ if pure guess",
        ]

        if client_context:
            background.append(f"CONTEXT: {client_context}")

        background.extend([
            "",
            "You are a persona extraction expert.",
            "Your job is to identify the target buyer persona and product category OF THE PROSPECT COMPANY.",
            "You analyze company websites and industry data to determine who makes purchasing decisions.",
            "IMPORTANT: The persona/product you identify is what the PROSPECT company sells, not what YOUR client sells.",
            "CRITICAL: Be honest about what you can verify from website_content vs what is inferred.",
        ])

        system_prompt_generator = SystemPromptGenerator(
            background=background,
            steps=[
                "1. Review the company name, website, and industry.",
                "2. IF website_content is provided:",
                "   - Analyze it for persona clues (job titles, team page, about page)",
                "   - Look for decision-maker mentions",
                "   - Extract product/service description",
                "   - Set confidence_score = 5, fallback_level = 0",
                "3. IF website_content is EMPTY or has no persona info:",
                "   - Use industry + company name for educated guess",
                "   - Set confidence_score = 3, fallback_level = 2",
                "4. Identify the primary decision-maker persona (specific title).",
                "5. Determine the product/service category they sell (specific).",
            ],
            output_instructions=[
                "GOOD EXAMPLES (specific, French):",
                "✅ target_persona: 'VP Sales' | product_category: 'plateforme de prospection B2B automatisée'",
                "✅ target_persona: 'Directeur Commercial' | product_category: 'logiciel de gestion de la relation client (CRM)'",
                "✅ target_persona: 'CTO' | product_category: 'solution de cybersécurité cloud'",
                "✅ target_persona: 'DRH' | product_category: 'plateforme de recrutement et gestion des talents'",
                "",
                "BAD EXAMPLES:",
                "❌ target_persona: 'executive' (too generic)",
                "❌ target_persona: 'decision maker' (too vague)",
                "❌ product_category: 'software' (too vague)",
                "❌ product_category: 'services' (too generic)",
                "",
                "Return JSON with target_persona and product_category.",
                "Use specific job titles from website content when available.",
                "Product category should be detailed: 'plateforme de X' not just 'software'.",
                "Set fallback_level: 0 if found on website, 2 if industry guess, 3+ if pure guess.",
                "Provide clear reasoning for your choice.",
            ],
        )

        config = AgentConfig(
            client=client,
            model=final_model,
            history=ChatHistory(),
            system_prompt_generator=system_prompt_generator,
        )

        self.agent = AtomicAgent[PersonaExtractorInputSchema, PersonaExtractorOutputSchema](config=config)
        self.enable_scraping = enable_scraping

    def run(self, input_data: PersonaExtractorInputSchema) -> PersonaExtractorOutputSchema:
        """
        Run persona extraction with optional auto-scraping.

        Args:
            input_data: Company data

        Returns:
            PersonaExtractorOutputSchema
        """
        # Auto-scrape if enabled and no content provided
        if self.enable_scraping and not input_data.website_content and input_data.website:
            try:
                scraped = scrape_for_agent_sync("persona_extractor", input_data.website)
                # IMPROVED: Scrape pages where persona/team info appears
                content_parts = [
                    scraped.get("/", ""),              # Homepage
                    scraped.get("/about", ""),         # About page (often has team info)
                    scraped.get("/a-propos", ""),      # French about
                    scraped.get("/qui-sommes-nous", ""), # French about
                    scraped.get("/team", ""),          # Team page
                    scraped.get("/equipe", ""),        # French team
                    scraped.get("/leadership", ""),    # Leadership page
                    scraped.get("/company", ""),       # Company page
                ]
                combined = "\n\n=== PAGE SEPARATOR ===\n\n".join([c for c in content_parts if c])
                input_data.website_content = preprocess_scraped_content(combined, max_tokens=5000)
            except Exception:
                pass  # Continue without scraping

        return self.agent.run(user_input=input_data)


class CompetitorFinderAgentOptimized:
    """
    Optimized CompetitorFinderAgent with Gemini Flash.

    Cost: $0.0002 (vs $0.015 with GPT-4o) = 99% savings
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_scraping: bool = True,
        client_context: Optional[str] = None
    ):
        client, final_model = create_openrouter_client(
            api_key=api_key,
            model_name=model,
            agent_type="competitor_finder"
        )

        background = [
            "⚠️ CRITICAL INSTRUCTION - WILL BE EVALUATED ⚠️",
            "You MUST respond EXCLUSIVELY in FRENCH (français).",
            "EVERY SINGLE WORD must be in French.",
            "If you use ANY English word, the response will be REJECTED.",
            "No exceptions. French only. Français uniquement.",
        ]

        if client_context:
            background.append(f"CONTEXT: {client_context}")

        background.extend([
            "You are a competitive intelligence expert.",
            "Your job is to identify the main competitor that the prospect likely uses FOR THEIR PRODUCT.",
            "You analyze the product category and industry to determine which competitor is most relevant.",
            "IMPORTANT: Find competitors of the PROSPECT's product, not competitors of YOUR client.",
        ])

        system_prompt_generator = SystemPromptGenerator(
            background=background,
            steps=[
                "1. Review the product category (e.g., 'CRM Software', 'Marketing Automation').",
                "2. Identify the market-leading competitor in that category.",
                "3. If website content is available, look for competitor mentions or technology stack clues.",
                "4. Return the competitor name and confirm product category.",
            ],
            output_instructions=[
                "Return JSON with competitor_name and competitor_product_category.",
                "Use real competitor names (e.g., 'Salesforce', 'HubSpot', not generic 'CRM Provider').",
                "Set fallback_level based on confidence.",
            ],
        )

        config = AgentConfig(
            client=client,
            model=final_model,
            history=ChatHistory(),
            system_prompt_generator=system_prompt_generator,
        )

        self.agent = AtomicAgent[CompetitorFinderInputSchema, CompetitorFinderOutputSchema](config=config)
        self.enable_scraping = enable_scraping

    def run(self, input_data: CompetitorFinderInputSchema) -> CompetitorFinderOutputSchema:
        if self.enable_scraping and not input_data.website_content and input_data.website:
            try:
                scraped = scrape_for_agent_sync("competitor_finder", input_data.website)
                # Combine pricing + features pages
                content_parts = [scraped.get(page, "") for page in ["/pricing", "/features"]]
                combined = "\n\n".join(content_parts)
                input_data.website_content = preprocess_scraped_content(combined, max_tokens=5000)
            except Exception:
                pass

        return self.agent.run(user_input=input_data)


class PainPointAgentOptimized:
    """
    Optimized PainPointAgent with GPT-4o-mini.

    Cost: $0.0003 (vs $0.015 with GPT-4o) = 98% savings
    UPGRADED: Using GPT-4o-mini for better French quality (was cheap model)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_scraping: bool = True,
        client_context: Optional[dict] = None  # CHANGED: Accept dict not str
    ):
        # UPGRADED: Force GPT-4o-mini for better French quality
        client, final_model = create_openrouter_client(
            api_key=api_key,
            model_name=model or "openai/gpt-4o-mini",  # Force GPT-4o-mini
            agent_type=None  # Disable auto-routing
        )

        background = [
            "⚠️ CRITICAL INSTRUCTION - WILL BE EVALUATED ⚠️",
            "You MUST respond EXCLUSIVELY in FRENCH (français).",
            "EVERY SINGLE WORD must be in French.",
            "If you use ANY English word, the response will be REJECTED.",
            "No exceptions. French only. Français uniquement.",
            "",
            "🚨 BANNED ENGLISH WORDS - USE FRENCH EQUIVALENTS 🚨",
            "❌ 'leads' → ✅ 'prospects'",
            "❌ 'pipeline' → ✅ 'tunnel de conversion' or 'pipeline commercial' (acceptable)",
            "❌ 'automation' → ✅ 'automatisation'",
            "❌ 'sales' → ✅ 'ventes' or 'commercial'",
            "❌ 'business' → ✅ 'entreprise' or 'activité'",
            "❌ 'growth' → ✅ 'croissance'",
            "❌ 'ROI' → ✅ 'retour sur investissement' or 'rentabilité'",
        ]

        # NEW: Parse structured client context
        if client_context and isinstance(client_context, dict):
            client_name = client_context.get("client_name", "le client")
            client_offerings = client_context.get("offerings", [])
            pain_solved = client_context.get("pain_solved", "développement commercial")
            target_industries = client_context.get("target_industries", [])

            context_str = f"""
🎯 CRITICAL CONTEXT - YOU WORK FOR: {client_name}

WHAT YOUR CLIENT SELLS/OFFERS:
{chr(10).join(f'- {offering}' for offering in client_offerings) if client_offerings else '- Solutions de développement commercial'}

THE MAIN PROBLEM YOUR CLIENT SOLVES:
{pain_solved}

TARGET INDUSTRIES:
{', '.join(target_industries) if target_industries else 'B2B companies'}

YOUR TASK:
You are analyzing the PROSPECT company (the potential customer).
You need to identify a pain point that the PROSPECT has RELATED TO:
- Needing MORE CLIENTS for their business
- Struggling with CLIENT ACQUISITION / LEAD GENERATION
- Difficulty GENERATING PROSPECTS for their services
- Low conversion rates, long sales cycles, manual prospecting
- Pipeline that's not growing fast enough

The pain point MUST be something {client_name} can solve with their offerings.

WRONG APPROACH (DON'T DO THIS):
❌ Internal operational problems (unless client sells ops solutions)
❌ HR/recruitment issues (unless client sells HR solutions)
❌ Technical infrastructure issues (unless client sells tech solutions)
❌ Employee management problems (unless client sells HR/management solutions)

CORRECT APPROACH (DO THIS):
✅ "difficulté à acquérir de nouveaux clients pour leurs services"
✅ "prospection manuelle qui consomme trop de temps"
✅ "taux de conversion faible sur les campagnes de prospection"
✅ "pipeline commercial qui se vide trop vite"
✅ "manque de prospects qualifiés pour alimenter les ventes"
✅ "processus de génération de leads inefficace"

REMEMBER: The prospect's problem is about GETTING MORE CUSTOMERS, not internal operations.
"""
            background.append(context_str)
        else:
            # Fallback if no structured context
            background.append("CONTEXT: You work for a B2B lead generation company. Focus on prospect's client acquisition challenges.")

        background.extend([
            "",
            "You are a pain point identification expert.",
            "Your job is to identify the specific problem the target persona faces THAT YOUR CLIENT'S PRODUCT CAN SOLVE.",
            "CRITICAL: The pain point must relate to CLIENT ACQUISITION, LEAD GENERATION, or SALES GROWTH.",
            "CRITICAL: Focus on the prospect's struggle to GET MORE CUSTOMERS, not their internal operations.",
        ])

        system_prompt_generator = SystemPromptGenerator(
            background=background,
            steps=[
                "1. Review the target persona and product category OF THE PROSPECT.",
                "2. Review the CLIENT CONTEXT to understand what the client sells.",
                "3. Identify the PROSPECT's main challenge RELATED TO CLIENT ACQUISITION:",
                "   - Do they struggle to find new customers?",
                "   - Is their prospecting process manual/inefficient?",
                "   - Do they have low conversion rates?",
                "   - Is their commercial pipeline not growing fast enough?",
                "4. Frame the pain point in terms of CLIENT ACQUISITION challenges.",
                "5. If website content is available, use it to understand the prospect's business model.",
                "6. Quantify the impact in measurable terms (time, money, productivity).",
                "7. VERIFY: Is this pain point related to CLIENT ACQUISITION? If not, reformulate.",
            ],
            output_instructions=[
                "⚠️ FRENCH ONLY - BANNED WORDS ⚠️",
                "❌ 'leads' → ✅ 'prospects'",
                "❌ 'pipeline' → ✅ 'tunnel de conversion' or 'pipeline commercial'",
                "❌ 'automation' → ✅ 'automatisation'",
                "",
                "GOOD EXAMPLES (100% French, lowercase, client acquisition focus):",
                "✅ 'la difficulté à acquérir de nouveaux prospects qualifiés'",
                "✅ 'la prospection manuelle qui consomme 15h par semaine'",
                "✅ 'le taux de conversion faible de vos campagnes commerciales'",
                "✅ 'le manque de prospects qualifiés pour alimenter les ventes'",
                "",
                "BAD EXAMPLES:",
                "❌ 'la difficulté de générer des leads' (English word 'leads')",
                "❌ 'des processus RH inefficaces' (not related to client acquisition)",
                "❌ 'La prospection manuelle' (starts with capital)",
                "❌ 'la prospection manuelle.' (has period at end)",
                "",
                "⚠️ TEMPLATE CONTEXT: Your output will be inserted into an email template.",
                "CRITICAL CAPITALIZATION RULES:",
                "- Start with LOWERCASE for problem_specific (e.g., 'la prospection manuelle' NOT 'La prospection manuelle')",
                "- NO period at the end (template adds punctuation)",
                "- Create a FRAGMENT, not a complete sentence",
                "",
                "Example template: 'En tant que {{persona}}, tu fais face à {{problem}}'",
                "Correct problem: 'la difficulté à acquérir de nouveaux prospects qualifiés'",
                "WRONG problem: 'La difficulté de générer des leads qualifiés.'",
                "",
                "Return JSON with problem_specific and impact_measurable.",
                "Be specific about CLIENT ACQUISITION problems, not internal operations.",
                "Impact should be quantified: '50% de perte de temps', '100K€ de revenus perdus'.",
            ],
        )

        config = AgentConfig(
            client=client,
            model=final_model,
            history=ChatHistory(),
            system_prompt_generator=system_prompt_generator,
        )

        self.agent = AtomicAgent[PainPointInputSchema, PainPointOutputSchema](config=config)
        self.enable_scraping = enable_scraping

    def run(self, input_data: PainPointInputSchema) -> PainPointOutputSchema:
        # REMOVED: Scraping prospect's site is not useful for identifying client acquisition pain points
        # The pain point should be inferred from:
        # 1. Client context (what problem the client solves)
        # 2. Prospect's persona + industry
        # 3. General B2B knowledge
        #
        # Scraping prospect's /customers or /testimonials doesn't help because:
        # - Prospects don't list their own problems on their site
        # - We need to identify THEIR need for more customers, not their existing customer problems

        # If scraping is needed, it should be to understand the prospect's business model,
        # not to find their pain points
        if self.enable_scraping and not input_data.website_content and input_data.website:
            try:
                scraped = scrape_for_agent_sync("pain_point", input_data.website)
                # Only scrape homepage to understand their business
                homepage = scraped.get("/", "")
                input_data.website_content = preprocess_scraped_content(homepage, max_tokens=2000)
            except Exception:
                pass

        return self.agent.run(user_input=input_data)


class SignalGeneratorAgentOptimized:
    """
    Optimized SignalGeneratorAgent with GPT-4o for factual accuracy.

    Cost: $0.0025 (vs $0.015 with GPT-4o standard) = 83% savings
    UPGRADED: Using GPT-4o to prevent hallucinations (was GPT-4o-mini)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_scraping: bool = True,
        client_context: Optional[str] = None
    ):
        # UPGRADED: Force GPT-4o for better factual accuracy (prevent hallucinations)
        client, final_model = create_openrouter_client(
            api_key=api_key,
            model_name=model or "openai/gpt-4o",  # Force GPT-4o if not specified
            agent_type=None  # Disable auto-routing
        )

        background = [
            "⚠️ CRITICAL INSTRUCTION - WILL BE EVALUATED ⚠️",
            "You MUST respond EXCLUSIVELY in FRENCH (français).",
            "EVERY SINGLE WORD must be in French.",
            "If you use ANY English word, the response will be REJECTED.",
            "No exceptions. French only. Français uniquement.",
            "",
            "🚨 CRITICAL ANTI-HALLUCINATION RULES 🚨",
            "",
            "RULE 1: ONLY USE FACTUAL INFORMATION FROM WEBSITE_CONTENT",
            "- If website_content mentions funding → use it verbatim",
            "- If website_content mentions hiring → use exact details",
            "- If website_content mentions product launch → use it",
            "- If website_content is EMPTY or has NO signals → use GENERIC fallback",
            "",
            "RULE 2: NEVER INVENT SPECIFIC NUMBERS OR FACTS",
            "- ❌ NEVER: 'vient de lever 2M€' (if not on website)",
            "- ❌ NEVER: 'recrute activement 10 commerciaux' (if not verified)",
            "- ❌ NEVER: 'vient d'ouvrir un bureau à Paris' (if not confirmed)",
            "- ✅ OK: 'développe son équipe commerciale' (generic if industry hints)",
            "- ✅ OK: 'cherche à augmenter sa visibilité' (generic for all B2B)",
            "",
            "RULE 3: USE FALLBACK GENERIC SIGNALS IF NOTHING FOUND",
            "Generic signals for B2B companies:",
            "- 'cherche à développer son activité commerciale'",
            "- 'souhaite optimiser sa génération de prospects'",
            "- 'vise à augmenter son pipeline commercial'",
            "- 'développe sa présence sur son marché'",
            "",
            "RULE 4: SET CONFIDENCE SCORE HONESTLY",
            "- confidence_score = 5: Found specific signal on website (exact quote)",
            "- confidence_score = 3: Inferred from industry/context (not explicit)",
            "- confidence_score = 1: Generic fallback (no specific data found)",
            "- fallback_level = 0 if real signals, 3 if generic",
        ]

        if client_context:
            background.append(f"CONTEXT: {client_context}")

        background.extend([
            "",
            "You are a buying signal detection expert.",
            "Your job is to identify specific signals that indicate the prospect is ready to buy YOUR CLIENT'S PRODUCT.",
            "You analyze company data and website content for trigger events RELEVANT TO YOUR CLIENT'S OFFERING.",
            "CRITICAL: Be honest about what you can and cannot verify from the website content.",
        ])

        system_prompt_generator = SystemPromptGenerator(
            background=background,
            steps=[
                "1. Review company name, industry, and website.",
                "2. Read website_content CAREFULLY for FACTUAL signals:",
                "   - Funding announcements (exact amounts, series, dates)",
                "   - Hiring (specific open positions, team expansion mentions)",
                "   - Product launches (new features, releases, announcements)",
                "   - Geographic expansion (new offices, markets)",
                "   - Press mentions (awards, partnerships, media coverage)",
                "3. IF YOU FIND FACTUAL SIGNALS in website_content:",
                "   - Use them verbatim (extract exact quotes)",
                "   - Set confidence_score = 5",
                "   - Set fallback_level = 0",
                "4. IF YOU FIND NO SPECIFIC SIGNALS in website_content:",
                "   - Use GENERIC industry-appropriate signals",
                "   - Set confidence_score = 1",
                "   - Set fallback_level = 3",
                "5. Generate 2 signals (use real if found, generic if not)",
                "6. Generate 2 targets/goals (realistic for this industry)",
            ],
            output_instructions=[
                "⚠️ ANTI-HALLUCINATION: NEVER INVENT SPECIFIC DATA ⚠️",
                "",
                "IF WEBSITE_CONTENT HAS SPECIFIC SIGNALS:",
                "✅ USE: 'vient de lever 2M€ en série A' (ONLY if mentioned on website)",
                "✅ USE: 'recrute 5 commerciaux selon leur page carrières' (ONLY if verified)",
                "",
                "IF WEBSITE_CONTENT HAS NO SPECIFIC SIGNALS:",
                "✅ USE: 'cherche à développer son activité commerciale'",
                "✅ USE: 'souhaite optimiser sa prospection B2B'",
                "✅ USE: 'vise à augmenter son taux de conversion'",
                "",
                "FORBIDDEN (unless verified on website):",
                "❌ 'vient de lever X€'",
                "❌ 'recrute X personnes'",
                "❌ 'vient d'ouvrir à [ville]'",
                "❌ Any specific number, amount, or location",
                "",
                "⚠️ TEMPLATE CONTEXT: Outputs will be inserted into email template.",
                "CRITICAL CAPITALIZATION RULES:",
                "- Start with LOWERCASE (e.g., 'cherche à développer' NOT 'Cherche à développer')",
                "- NO period/punctuation at the end (template adds punctuation)",
                "- Create a FRAGMENT that flows naturally when inserted mid-sentence",
                "",
                "Example template: 'J'ai vu que {{company}} {{signal}}'",
                "Correct signal: 'cherche à développer son activité'",
                "WRONG signal: 'Cherche à développer son activité.'",
                "",
                "Return JSON with specific_signal_1, specific_signal_2, specific_target_1, specific_target_2.",
                "If no factual signals found, use GENERIC statements (set confidence_score = 1, fallback_level = 3).",
            ],
        )

        config = AgentConfig(
            client=client,
            model=final_model,
            history=ChatHistory(),
            system_prompt_generator=system_prompt_generator,
        )

        self.agent = AtomicAgent[SignalGeneratorInputSchema, SignalGeneratorOutputSchema](config=config)
        self.enable_scraping = enable_scraping

    def run(self, input_data: SignalGeneratorInputSchema) -> SignalGeneratorOutputSchema:
        if self.enable_scraping and not input_data.website_content and input_data.website:
            try:
                scraped = scrape_for_agent_sync("signal_generator", input_data.website)
                # IMPROVED: Scrape pages where buying signals actually appear
                content_parts = [
                    scraped.get("/", ""),              # Homepage
                    scraped.get("/blog", ""),          # Blog posts
                    scraped.get("/news", ""),          # News/press
                    scraped.get("/actualites", ""),    # French news
                    scraped.get("/press", ""),         # Press releases
                    scraped.get("/presse", ""),        # French press
                    scraped.get("/careers", ""),       # Job postings (hiring signals)
                    scraped.get("/jobs", ""),          # Jobs
                    scraped.get("/carrieres", ""),     # French careers
                    scraped.get("/about", ""),         # About page (funding, history)
                ]
                combined = "\n\n=== PAGE SEPARATOR ===\n\n".join([c for c in content_parts if c])
                input_data.website_content = preprocess_scraped_content(combined, max_tokens=5000)
            except Exception:
                pass

        return self.agent.run(user_input=input_data)


class SystemBuilderAgentOptimized:
    """
    Optimized SystemBuilderAgent with DeepSeek.

    Cost: $0.0001 (vs $0.015 with GPT-4o) = 99% savings
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_scraping: bool = True,
        client_context: Optional[str] = None
    ):
        client, final_model = create_openrouter_client(
            api_key=api_key,
            model_name=model,
            agent_type="system_builder"
        )

        background = [
            "⚠️ CRITICAL INSTRUCTION - WILL BE EVALUATED ⚠️",
            "You MUST respond EXCLUSIVELY in FRENCH (français).",
            "EVERY SINGLE WORD must be in French.",
            "If you use ANY English word, the response will be REJECTED.",
            "No exceptions. French only. Français uniquement.",
        ]

        if client_context:
            background.append(f"CONTEXT: {client_context}")

        background.extend([
            "You are a systems/processes identification expert.",
            "Your job is to identify which internal systems/processes the prospect uses FOR THEIR BUSINESS OPERATIONS.",
            "You analyze the industry and product category to determine likely tech stack and workflows.",
        ])

        system_prompt_generator = SystemPromptGenerator(
            background=background,
            steps=[
                "1. Review company industry and product category.",
                "2. Identify 3 specific systems/processes they likely use.",
                "3. If website content (integrations/API) is available, extract actual systems mentioned.",
            ],
            output_instructions=[
                "Return JSON with system_1, system_2, system_3.",
                "Be specific: 'Salesforce CRM', 'Slack for communication' not 'CRM tool', 'Chat tool'.",
            ],
        )

        config = AgentConfig(
            client=client,
            model=final_model,
            history=ChatHistory(),
            system_prompt_generator=system_prompt_generator,
        )

        self.agent = AtomicAgent[SystemBuilderInputSchema, SystemBuilderOutputSchema](config=config)
        self.enable_scraping = enable_scraping

    def run(self, input_data: SystemBuilderInputSchema) -> SystemBuilderOutputSchema:
        if self.enable_scraping and not input_data.website_content and input_data.website:
            try:
                scraped = scrape_for_agent_sync("system_builder", input_data.website)
                content_parts = [scraped.get(page, "") for page in ["/integrations", "/api"]]
                combined = "\n\n".join(content_parts)
                input_data.website_content = preprocess_scraped_content(combined, max_tokens=5000)
            except Exception:
                pass

        return self.agent.run(user_input=input_data)


class CaseStudyAgentOptimized:
    """
    Optimized CaseStudyAgent with GPT-4o-mini.

    Cost: $0.0003 (vs $0.015 with GPT-4o) = 98% savings
    UPGRADED: Using GPT-4o-mini with grounding (was cheap model)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_scraping: bool = True,
        client_context: Optional[dict] = None  # CHANGED: Accept dict not str
    ):
        # UPGRADED: Force GPT-4o-mini
        client, final_model = create_openrouter_client(
            api_key=api_key,
            model_name=model or "openai/gpt-4o-mini",  # Force GPT-4o-mini
            agent_type=None  # Disable auto-routing
        )

        background = [
            "⚠️ CRITICAL INSTRUCTION - WILL BE EVALUATED ⚠️",
            "You MUST respond EXCLUSIVELY in FRENCH (français).",
            "EVERY SINGLE WORD must be in French.",
            "If you use ANY English word, the response will be REJECTED.",
            "No exceptions. French only. Français uniquement.",
            "",
            "🚨 CRITICAL ANTI-HALLUCINATION RULES 🚨",
            "",
            "RULE 1: USE REAL CASE STUDIES IF PROVIDED",
            "- If client_context includes real case studies → adapt one to this prospect",
            "- If real case studies provided → use REAL company names and metrics",
            "",
            "RULE 2: IF NO REAL DATA, USE GENERIC FALLBACK",
            "- ❌ NEVER: 'TechCo à augmenter son pipeline de 300% en 6 mois' (if not real)",
            "- ❌ NEVER: Fake company names (TechCo, StartupX, EntrepriseY)",
            "- ❌ NEVER: Fake metrics (300%, 6 mois, 50K€) if not verified",
            "- ✅ OK: 'des entreprises similaires à optimiser significativement leur prospection'",
            "- ✅ OK: 'des acteurs du [industry] à améliorer leur acquisition de clients'",
            "",
            "RULE 3: SET CONFIDENCE SCORE HONESTLY",
            "- confidence_score = 5: Real case study from client",
            "- confidence_score = 1: Generic fallback (no real data)",
            "- fallback_level = 0 if real case study, 3 if generic",
        ]

        # NEW: Parse structured client context for real case studies
        if client_context and isinstance(client_context, dict):
            client_name = client_context.get("client_name", "le client")
            real_case_studies = client_context.get("real_case_studies", [])

            if real_case_studies:
                # Format real case studies for the agent
                case_studies_str = "\n".join([
                    f"- {cs.get('company', 'Entreprise')} : {cs.get('result', '')}"
                    for cs in real_case_studies
                ])
                context_str = f"""
🎯 REAL CASE STUDIES FROM {client_name}:

{case_studies_str}

USE THESE REAL CASE STUDIES:
- Select the most relevant one for this prospect
- You can adapt it slightly to match their industry
- Use REAL company names and metrics from above
- Set confidence_score = 5, fallback_level = 0
"""
            else:
                # No real case studies provided
                context_str = f"""
🎯 CONTEXT: You work for {client_name}

NO REAL CASE STUDIES PROVIDED.

YOU MUST USE GENERIC FALLBACK:
- 'des entreprises similaires à optimiser leur génération de prospects'
- 'des acteurs du [industry] à améliorer significativement leur acquisition de clients'
- 'plusieurs entreprises [industry] à augmenter leur pipeline commercial'

DO NOT invent fake company names or fake metrics.
Set confidence_score = 1, fallback_level = 3
"""
            background.append(context_str)
        else:
            # Fallback if no context
            background.append("NO REAL CASE STUDIES PROVIDED. Use generic template only.")

        background.extend([
            "",
            "You are a case study crafting expert.",
            "Your job is to create a compelling result statement showing how YOUR CLIENT helped a similar company.",
            "CRITICAL: Use REAL case studies if provided, otherwise use GENERIC template.",
            "CRITICAL: The case study must show YOUR CLIENT solving the problem, not the prospect.",
        ])

        system_prompt_generator = SystemPromptGenerator(
            background=background,
            steps=[
                "1. Review the problem_specific and impact_measurable.",
                "2. Check if REAL CASE STUDIES are provided in the context.",
                "3. IF REAL CASE STUDIES PROVIDED:",
                "   - Select the most relevant one for this prospect's industry",
                "   - Use REAL company names and metrics",
                "   - Adapt slightly to match prospect's context",
                "   - Set confidence_score = 5, fallback_level = 0",
                "4. IF NO REAL CASE STUDIES:",
                "   - Use GENERIC template",
                "   - 'des entreprises similaires à [outcome]'",
                "   - NO fake company names (TechCo, StartupX, etc.)",
                "   - NO fake metrics (300%, 6 mois, etc.)",
                "   - Set confidence_score = 1, fallback_level = 3",
                "5. Create a result that directly addresses the problem.",
            ],
            output_instructions=[
                "⚠️ ANTI-HALLUCINATION: USE REAL DATA OR GENERIC TEMPLATE ⚠️",
                "",
                "IF REAL CASE STUDIES PROVIDED IN CONTEXT:",
                "✅ 'Salesforce France à augmenter son pipeline de 300% en 6 mois' (ONLY if real)",
                "✅ 'Hub France à réduire leur temps de prospection de 50%' (ONLY if real)",
                "",
                "IF NO REAL CASE STUDIES:",
                "✅ 'des entreprises similaires à optimiser significativement leur prospection'",
                "✅ 'des acteurs du secteur RH à améliorer leur acquisition de clients'",
                "✅ 'plusieurs entreprises du secteur à augmenter leur pipeline commercial'",
                "",
                "FORBIDDEN (unless real case study):",
                "❌ 'TechCo à augmenter...' (fake company name)",
                "❌ 'StartupX à améliorer...' (fake company name)",
                "❌ '300%', '6 mois', '50K€' (fake metrics)",
                "",
                "⚠️ TEMPLATE CONTEXT: Your output appears after 'On a aidé:'",
                "CRITICAL CAPITALIZATION RULES:",
                "- Start with UPPERCASE if company name (e.g., 'Salesforce France')",
                "- Start with lowercase if generic (e.g., 'des entreprises similaires')",
                "- NO period at the end (template adds punctuation)",
                "",
                "Example template: 'On a aidé: {{case_study}}'",
                "Correct: 'des entreprises similaires à optimiser leur prospection'",
                "WRONG: 'TechCo à augmenter son pipeline de 300%' (if not real)",
                "",
                "Return JSON with case_study_result.",
                "If no real data, use GENERIC template. NEVER invent companies or metrics.",
            ],
        )

        config = AgentConfig(
            client=client,
            model=final_model,
            history=ChatHistory(),
            system_prompt_generator=system_prompt_generator,
        )

        self.agent = AtomicAgent[CaseStudyInputSchema, CaseStudyOutputSchema](config=config)
        self.enable_scraping = enable_scraping

    def run(self, input_data: CaseStudyInputSchema) -> CaseStudyOutputSchema:
        # REMOVED: Scraping prospect's site for case studies doesn't make sense
        # We should use the CLIENT's case studies, not the prospect's
        # The real case studies should be passed in client_context during __init__
        #
        # If we wanted to scrape, it should be the CLIENT's website (once, cached),
        # not the prospect's website (every time)

        return self.agent.run(user_input=input_data)
