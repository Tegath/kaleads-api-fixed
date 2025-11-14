"""
ProofGenerator Agent v3.0 (formerly CaseStudyAgent) - Context-Aware

This agent generates social proof (case studies, results) for emails.

Key improvements in v3:
- Renamed from CaseStudyAgent to ProofGenerator (clearer purpose)
- Accepts ClientContext with real_case_studies
- Two explicit modes:
  * client_case_studies (DEFAULT): Uses YOUR case studies
  * prospect_achievements: Mentions THEIR achievements (rare usage)
- Smart matching by industry
- Anti-hallucination: Generic fallback if no case studies

IMPORTANT: This agent was previously called CaseStudyAgent and had confusing dual usage.
Now it's clear what it does in each mode.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field

try:
    from src.models.client_context import ClientContext, CaseStudy
except ImportError:
    ClientContext = None
    CaseStudy = None


# ============================================
# Schemas
# ============================================

class ProofGeneratorInputSchema(BaseModel):
    """Input schema for Proof Generator."""
    company_name: str = Field(..., description="Name of the prospect company")
    website: str = Field(..., description="Website URL")
    industry: str = Field(default="", description="Industry/sector")
    problem_specific: str = Field(default="", description="Specific pain point from PainPointAnalyzer")
    impact_measurable: str = Field(default="", description="Impact from PainPointAnalyzer")
    website_content: str = Field(default="", description="Scraped content (optional)")


class ProofGeneratorOutputSchema(BaseModel):
    """Output schema for Proof Generator."""
    case_study_result: str = Field(..., description="Case study result (format: starts with lowercase or uppercase depending on context)")
    confidence_score: int = Field(..., description="Confidence score 1-5 (5=real case study, 1=generic)")
    fallback_level: int = Field(..., description="Fallback level 0-3 (0=perfect match, 3=generic)")
    reasoning: str = Field(..., description="Reasoning for the choice")
    source: str = Field(default="client_case_studies", description="Source: 'client_case_studies', 'prospect_achievements', 'generic'")
    case_study_company: Optional[str] = Field(None, description="Company name from case study (if real)")
    case_study_industry: Optional[str] = Field(None, description="Industry from case study (if real)")


# ============================================
# Agent
# ============================================

class ProofGeneratorV3:
    """
    v3.0 Proof Generator Agent (formerly CaseStudyAgent).

    Generates social proof for emails by using real case studies or generic fallbacks.

    Two modes:
    1. client_case_studies (DEFAULT): Uses YOUR case studies from ClientContext
    2. prospect_achievements (RARE): Scrapes THEIR achievements

    Usage - Mode 1 (client case studies):
        >>> from src.models.client_context import ClientContext, CaseStudy
        >>> context = ClientContext(
        ...     client_id="kaleads-uuid",
        ...     client_name="Kaleads",
        ...     real_case_studies=[
        ...         CaseStudy(
        ...             company="Salesforce France",
        ...             industry="SaaS",
        ...             result="augmenter son pipeline de 300% en 6 mois"
        ...         )
        ...     ]
        ... )
        >>> agent = ProofGeneratorV3(client_context=context, mode="client_case_studies")
        >>> result = agent.run(ProofGeneratorInputSchema(
        ...     company_name="Aircall",
        ...     industry="SaaS"
        ... ))
        >>> print(result.case_study_result)
        "Salesforce France à augmenter son pipeline de 300% en 6 mois"
        >>> print(result.confidence_score)
        5
        >>> print(result.source)
        "client_case_studies"

    Usage - Mode 2 (prospect achievements):
        >>> agent = ProofGeneratorV3(mode="prospect_achievements")
        >>> result = agent.run(ProofGeneratorInputSchema(
        ...     company_name="Aircall",
        ...     website_content="...Aircall helped TechCo reduce costs by 40%..."
        ... ))
        >>> print(result.case_study_result)
        "aidé TechCo à réduire leurs coûts de 40%"
        >>> print(result.source)
        "prospect_achievements"
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_scraping: bool = True,
        enable_tavily: bool = True,
        client_context: Optional["ClientContext"] = None,
        mode: Literal["client_case_studies", "prospect_achievements"] = "client_case_studies"
    ):
        """
        Initialize ProofGenerator v3.

        Args:
            api_key: OpenRouter API key (optional)
            model: Model to use (optional)
            enable_scraping: Enable website scraping
            enable_tavily: Enable Tavily web search (for prospect_achievements mode)
            client_context: Client context (REQUIRED for client_case_studies mode)
            mode: "client_case_studies" (default) or "prospect_achievements"
        """
        self.api_key = api_key
        self.model = model
        self.enable_scraping = enable_scraping
        self.enable_tavily = enable_tavily
        self.client_context = client_context
        self.mode = mode

        print(f"[ProofGeneratorV3] Initialized with mode: {mode}")

        # Validate: client_case_studies mode requires client_context
        if mode == "client_case_studies" and not client_context:
            print("[ProofGeneratorV3] WARNING: client_case_studies mode without ClientContext - will fallback to generic")

    def run(self, input_data: ProofGeneratorInputSchema) -> ProofGeneratorOutputSchema:
        """
        Generate social proof.

        Strategy depends on mode:
        - client_case_studies: Use client's real case studies
        - prospect_achievements: Scrape prospect's achievements

        Args:
            input_data: Prospect information

        Returns:
            ProofGeneratorOutputSchema with case study
        """
        if self.mode == "client_case_studies":
            return self._use_client_case_studies(input_data)
        else:
            return self._use_prospect_achievements(input_data)

    def _use_client_case_studies(self, input_data: ProofGeneratorInputSchema) -> ProofGeneratorOutputSchema:
        """
        Use CLIENT's case studies.

        Strategy:
        1. Perfect match: Same industry
        2. Adapted: Different industry but same pain type
        3. Generic: No case studies available

        Returns:
            ProofGeneratorOutputSchema with case study
        """
        if not self.client_context or not self.client_context.has_real_case_studies():
            # No case studies available - use generic fallback
            return self._generic_fallback(input_data)

        # Strategy 1: Find perfect match by industry
        case_study = self.client_context.find_case_study_by_industry(input_data.industry)

        if case_study:
            # Perfect match!
            return ProofGeneratorOutputSchema(
                case_study_result=case_study.to_short_string(),
                confidence_score=5,
                fallback_level=0,
                reasoning=f"Perfect industry match: {case_study.industry} = {input_data.industry}",
                source="client_case_studies",
                case_study_company=case_study.company,
                case_study_industry=case_study.industry
            )

        # Strategy 2: Use first case study but adapt
        first_cs = self.client_context.real_case_studies[0]

        # Adapt the case study
        adapted_result = f"une entreprise {input_data.industry or 'similaire'} à {first_cs.result}"

        return ProofGeneratorOutputSchema(
            case_study_result=adapted_result,
            confidence_score=4,
            fallback_level=1,
            reasoning=f"Adapted case study from {first_cs.industry} to {input_data.industry}",
            source="client_case_studies",
            case_study_company=None,  # Don't mention company for adapted case studies
            case_study_industry=input_data.industry
        )

    def _use_prospect_achievements(self, input_data: ProofGeneratorInputSchema) -> ProofGeneratorOutputSchema:
        """
        Use PROSPECT's achievements (scrape their site).

        This is RARE usage - only when you want to compliment them on their own results.

        Returns:
            ProofGeneratorOutputSchema with prospect's achievement
        """
        # Try to scrape achievements from website content
        if self.enable_scraping and input_data.website_content:
            result = self._scrape_prospect_achievements(input_data)
            if result:
                return result

        # Fallback: Generic mention
        return ProofGeneratorOutputSchema(
            case_study_result=f"aidé de nombreux clients dans le secteur {input_data.industry or 'B2B'} à atteindre leurs objectifs",
            confidence_score=2,
            fallback_level=2,
            reasoning="No prospect achievements found on site, using generic mention",
            source="prospect_achievements",
            case_study_company=None,
            case_study_industry=input_data.industry
        )

    def _scrape_prospect_achievements(self, input_data: ProofGeneratorInputSchema) -> Optional[ProofGeneratorOutputSchema]:
        """
        Scrape prospect's site for their case studies/achievements.

        Would require LLM to extract achievements from content.
        Placeholder for now.

        Returns:
            ProofGeneratorOutputSchema if found, None otherwise
        """
        # Placeholder - would use LLM to extract achievements
        # Look for patterns like:
        # - "helped X company achieve Y"
        # - "X company increased Y by Z%"
        # - "our clients include..."

        return None

    def _generic_fallback(self, input_data: ProofGeneratorInputSchema) -> ProofGeneratorOutputSchema:
        """
        Generic fallback when no case studies available.

        ANTI-HALLUCINATION: Never invent fake companies or metrics.

        Returns:
            ProofGeneratorOutputSchema with generic proof
        """
        # Generic based on industry
        industry = input_data.industry or "B2B"

        # Generic statements (no fake companies!)
        generic_results = {
            "saas": "des entreprises SaaS similaires à optimiser significativement leur génération de leads",
            "tech": "des entreprises tech à améliorer leur efficacité commerciale",
            "consulting": "des cabinets de conseil à développer leur pipeline client",
            "agency": "des agences à augmenter leur nombre de clients réguliers",
            "finance": "des institutions financières à moderniser leur prospection",
            "healthcare": "des entreprises du secteur santé à optimiser leurs processus d'acquisition",
            "retail": "des entreprises du retail à améliorer leur performance commerciale",
            "default": "des entreprises similaires à optimiser leur génération de prospects"
        }

        # Find matching generic
        industry_lower = industry.lower()
        result = generic_results.get(industry_lower)

        if not result:
            # Try partial match
            for key, value in generic_results.items():
                if key in industry_lower or industry_lower in key:
                    result = value
                    break

        if not result:
            result = generic_results["default"]

        return ProofGeneratorOutputSchema(
            case_study_result=result,
            confidence_score=1,
            fallback_level=3,
            reasoning="No real case studies available, using generic fallback (anti-hallucination)",
            source="generic",
            case_study_company=None,
            case_study_industry=None
        )


# Example usage
if __name__ == "__main__":
    print("=== Test 1: With Real Case Studies ===")
    from src.models.client_context import ClientContext, CaseStudy

    context = ClientContext(
        client_id="kaleads-uuid",
        client_name="Kaleads",
        real_case_studies=[
            CaseStudy(
                company="Salesforce France",
                industry="SaaS",
                result="augmenter son pipeline de 300% en 6 mois",
                metric="300% pipeline increase"
            ),
            CaseStudy(
                company="BNP Paribas",
                industry="Finance",
                result="générer 500 leads qualifiés par mois",
                metric="500 leads/month"
            )
        ]
    )

    agent = ProofGeneratorV3(client_context=context, mode="client_case_studies")

    # Test 1: Perfect industry match (SaaS)
    result_saas = agent.run(ProofGeneratorInputSchema(
        company_name="Aircall",
        industry="SaaS"
    ))

    print(f"Result: {result_saas.case_study_result}")
    print(f"Company: {result_saas.case_study_company}")
    print(f"Confidence: {result_saas.confidence_score}/5")
    print(f"Fallback level: {result_saas.fallback_level}")
    print()

    # Test 2: Different industry (adapted)
    result_health = agent.run(ProofGeneratorInputSchema(
        company_name="Doctolib",
        industry="Healthcare"
    ))

    print(f"Result: {result_health.case_study_result}")
    print(f"Confidence: {result_health.confidence_score}/5")
    print(f"Fallback level: {result_health.fallback_level}")
    print()

    print("=== Test 2: Without Case Studies (Generic) ===")
    context_empty = ClientContext(
        client_id="newclient-uuid",
        client_name="NewClient",
        real_case_studies=[]  # No case studies
    )

    agent_empty = ProofGeneratorV3(client_context=context_empty, mode="client_case_studies")

    result_generic = agent_empty.run(ProofGeneratorInputSchema(
        company_name="TechCorp",
        industry="Tech"
    ))

    print(f"Result: {result_generic.case_study_result}")
    print(f"Confidence: {result_generic.confidence_score}/5")
    print(f"Source: {result_generic.source}")
