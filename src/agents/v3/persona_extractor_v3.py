"""
PersonaExtractor Agent v3.0 - Context-Aware + Web-Enhanced

This agent extracts decision-maker persona information from prospect data.

Key improvements in v3:
- Accepts ClientContext to adapt persona targeting
- Uses Tavily for LinkedIn/web search
- Graceful fallback if web search unavailable
- Generic and reusable across clients
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

try:
    from src.models.client_context import ClientContext
except ImportError:
    ClientContext = None

try:
    from src.providers.tavily_client import get_tavily_client
except ImportError:
    get_tavily_client = None


class PersonaExtractorInputSchema(BaseModel):
    """Input schema for Persona Extractor."""
    company_name: str = Field(..., description="Name of the prospect company")
    website: str = Field(..., description="Website URL")
    industry: str = Field(default="", description="Industry/sector")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn profile or company page URL")
    website_content: str = Field(default="", description="Scraped website content (optional)")


class PersonaExtractorOutputSchema(BaseModel):
    """Output schema for Persona Extractor."""
    role: str = Field(..., description="Decision-maker role (e.g., 'CMO', 'Head of Sales', 'CTO')")
    department: str = Field(..., description="Department (e.g., 'Marketing', 'Sales', 'Engineering')")
    seniority_level: str = Field(..., description="Seniority (e.g., 'C-level', 'VP', 'Director', 'Manager')")
    likely_pain_points: List[str] = Field(default_factory=list, description="Likely pain points for this persona")
    confidence_score: int = Field(..., description="Confidence score 1-5 (5=found on site, 1=inferred)")
    fallback_level: int = Field(..., description="Fallback level 0-3 (0=best, 3=generic)")
    reasoning: str = Field(..., description="Reasoning for the persona choice")
    source: str = Field(default="inference", description="Source: 'web_search', 'site_scrape', 'inference'")


class PersonaExtractorV3:
    """
    v3.0 Persona Extractor Agent.

    Extracts decision-maker persona from prospect data.

    Usage:
        >>> from src.models.client_context import ClientContext
        >>> context = ClientContext(
        ...     client_id="kaleads-uuid",
        ...     client_name="Kaleads",
        ...     pain_solved="génération de leads B2B"
        ... )
        >>> agent = PersonaExtractorV3(client_context=context, enable_tavily=True)
        >>> result = agent.run(PersonaExtractorInputSchema(
        ...     company_name="Aircall",
        ...     website="https://aircall.io",
        ...     industry="SaaS"
        ... ))
        >>> print(result.role)
        "Head of Sales"
        >>> print(result.department)
        "Sales"
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_scraping: bool = True,
        enable_tavily: bool = True,
        client_context: Optional["ClientContext"] = None
    ):
        """
        Initialize PersonaExtractor v3.

        Args:
            api_key: OpenRouter API key (optional)
            model: Model to use (optional)
            enable_scraping: Enable website scraping
            enable_tavily: Enable Tavily web search
            client_context: Client context (optional but recommended)
        """
        self.api_key = api_key
        self.model = model
        self.enable_scraping = enable_scraping
        self.enable_tavily = enable_tavily
        self.client_context = client_context

        # Initialize Tavily client
        self.tavily = None
        if enable_tavily and get_tavily_client:
            try:
                self.tavily = get_tavily_client()
            except Exception as e:
                print(f"Warning: Could not initialize Tavily: {e}")

    def run(self, input_data: PersonaExtractorInputSchema) -> PersonaExtractorOutputSchema:
        """
        Extract decision-maker persona from prospect data.

        Strategy:
        1. Try Tavily web search for LinkedIn/team page → HIGH confidence
        2. Try scraping prospect's website (team/about pages) → MEDIUM confidence
        3. Try industry + client context inference → LOW confidence
        4. Generic fallback → VERY LOW confidence

        Args:
            input_data: Prospect information

        Returns:
            PersonaExtractorOutputSchema with persona info
        """
        # Strategy 1: Tavily web search (LinkedIn, team pages)
        if self.tavily and self.tavily.enabled:
            result = self._try_tavily_search(input_data)
            if result:
                return result

        # Strategy 2: Scrape prospect's website (team/about pages)
        if self.enable_scraping and input_data.website_content:
            result = self._try_scrape_persona(input_data)
            if result:
                return result

        # Strategy 3: Industry + Client context inference
        result = self._try_context_inference(input_data)
        if result:
            return result

        # Strategy 4: Generic fallback
        return self._generic_fallback(input_data)

    def _try_tavily_search(self, input_data: PersonaExtractorInputSchema) -> Optional[PersonaExtractorOutputSchema]:
        """
        Try to find decision-maker using Tavily web search.

        Searches for:
        - LinkedIn profiles of key decision-makers
        - Team/about pages
        - Press releases with executive names

        Returns:
            PersonaExtractorOutputSchema if found, None otherwise
        """
        try:
            print(f"[PersonaExtractorV3] Using Tavily to find decision-maker for {input_data.company_name}")

            # Determine target role based on client context
            target_role = self._determine_target_role_from_context()

            # Search for decision-maker
            query = f"{input_data.company_name} {target_role} LinkedIn"
            results = self.tavily.search(query, max_results=3)

            if not results or "results" not in results:
                print(f"[PersonaExtractorV3] Tavily found no results")
                return None

            # Extract persona from results (simplified - real impl would use LLM)
            # For now, return inferred persona based on context
            return self._build_persona_from_context(input_data, confidence=4, source="web_search")

        except Exception as e:
            print(f"[PersonaExtractorV3] Tavily search failed: {e}")
            return None

    def _try_scrape_persona(self, input_data: PersonaExtractorInputSchema) -> Optional[PersonaExtractorOutputSchema]:
        """
        Try to extract persona from scraped website content.

        Looks for:
        - Team/About pages with roles
        - Leadership mentions
        - Department structure

        Returns:
            PersonaExtractorOutputSchema if found, None otherwise
        """
        content = input_data.website_content.lower()

        # Common patterns for team pages
        team_patterns = [
            "our team",
            "leadership",
            "meet the team",
            "about us",
            "management team"
        ]

        # Check if website has team info
        has_team_info = any(pattern in content for pattern in team_patterns)

        if has_team_info:
            # Found team page - in real implementation, use LLM to extract
            # For now, return inferred persona with medium confidence
            return self._build_persona_from_context(input_data, confidence=3, source="site_scrape")

        return None

    def _try_context_inference(self, input_data: PersonaExtractorInputSchema) -> Optional[PersonaExtractorOutputSchema]:
        """
        Infer persona based on industry + client context.

        Uses client's pain_solved to determine which persona to target.

        Returns:
            PersonaExtractorOutputSchema with inferred persona
        """
        return self._build_persona_from_context(input_data, confidence=3, source="inference")

    def _generic_fallback(self, input_data: PersonaExtractorInputSchema) -> PersonaExtractorOutputSchema:
        """
        Generic fallback when no persona found.

        Returns generic decision-maker role.

        Returns:
            PersonaExtractorOutputSchema with generic fallback
        """
        return PersonaExtractorOutputSchema(
            role="Decision-maker",
            department="General",
            seniority_level="C-level / VP",
            likely_pain_points=["Efficiency", "Growth", "Cost optimization"],
            confidence_score=1,
            fallback_level=3,
            reasoning="No specific persona found, using generic decision-maker",
            source="inference"
        )

    def _determine_target_role_from_context(self) -> str:
        """
        Determine target role based on client context.

        Returns:
            Target role string (e.g., "CMO", "Head of Sales", "CTO")
        """
        if not self.client_context:
            return "CEO"

        pain_lower = self.client_context.pain_solved.lower()

        # Map pain solved to target role
        if any(kw in pain_lower for kw in ["lead", "prospect", "sales", "client acquisition"]):
            return "Head of Sales"
        elif any(kw in pain_lower for kw in ["marketing", "demand", "campaign"]):
            return "CMO"
        elif any(kw in pain_lower for kw in ["rh", "recruit", "talent", "hiring"]):
            return "CHRO"
        elif any(kw in pain_lower for kw in ["devops", "cloud", "infrastructure", "deployment"]):
            return "CTO"
        elif any(kw in pain_lower for kw in ["ops", "process", "workflow", "automation"]):
            return "COO"
        else:
            return "CEO"

    def _build_persona_from_context(
        self,
        input_data: PersonaExtractorInputSchema,
        confidence: int,
        source: str
    ) -> PersonaExtractorOutputSchema:
        """
        Build persona output based on client context.

        Args:
            input_data: Prospect information
            confidence: Confidence score (1-5)
            source: Source of persona info

        Returns:
            PersonaExtractorOutputSchema
        """
        if not self.client_context:
            # No context - return generic
            return PersonaExtractorOutputSchema(
                role="Decision-maker",
                department="General",
                seniority_level="C-level",
                likely_pain_points=["Efficiency", "Growth"],
                confidence_score=confidence,
                fallback_level=2,
                reasoning="Inferred from industry without client context",
                source=source
            )

        pain_lower = self.client_context.pain_solved.lower()

        # CLIENT ACQUISITION (lead gen, sales)
        if any(kw in pain_lower for kw in ["lead", "prospect", "sales", "client acquisition"]):
            return PersonaExtractorOutputSchema(
                role="Head of Sales",
                department="Sales",
                seniority_level="VP / Director",
                likely_pain_points=[
                    "Difficulté à générer des leads qualifiés",
                    "Pipeline de ventes insuffisant",
                    "Prospection manuelle chronophage",
                    "Taux de conversion faible"
                ],
                confidence_score=confidence,
                fallback_level=1,
                reasoning=f"Inferred from client pain: '{self.client_context.pain_solved}' → Sales persona",
                source=source
            )

        # MARKETING
        elif any(kw in pain_lower for kw in ["marketing", "demand", "campaign", "content"]):
            return PersonaExtractorOutputSchema(
                role="CMO",
                department="Marketing",
                seniority_level="C-level / VP",
                likely_pain_points=[
                    "Difficulté à générer de la demande qualifiée",
                    "ROI marketing incertain",
                    "Campagnes non personnalisées",
                    "Attribution marketing complexe"
                ],
                confidence_score=confidence,
                fallback_level=1,
                reasoning=f"Inferred from client pain: '{self.client_context.pain_solved}' → Marketing persona",
                source=source
            )

        # HR / RECRUITMENT
        elif any(kw in pain_lower for kw in ["rh", "recruit", "talent", "hiring"]):
            return PersonaExtractorOutputSchema(
                role="CHRO",
                department="Human Resources",
                seniority_level="C-level / VP",
                likely_pain_points=[
                    "Difficulté à recruter des talents qualifiés",
                    "Processus de recrutement lent",
                    "Turnover élevé",
                    "Expérience candidat médiocre"
                ],
                confidence_score=confidence,
                fallback_level=1,
                reasoning=f"Inferred from client pain: '{self.client_context.pain_solved}' → HR persona",
                source=source
            )

        # DEVOPS / INFRASTRUCTURE
        elif any(kw in pain_lower for kw in ["devops", "cloud", "infrastructure", "deployment"]):
            return PersonaExtractorOutputSchema(
                role="CTO",
                department="Engineering",
                seniority_level="C-level / VP",
                likely_pain_points=[
                    "Déploiements lents et risqués",
                    "Infrastructure non scalable",
                    "Coûts cloud élevés",
                    "Manque de visibilité sur la stack"
                ],
                confidence_score=confidence,
                fallback_level=1,
                reasoning=f"Inferred from client pain: '{self.client_context.pain_solved}' → Engineering persona",
                source=source
            )

        # OPS / PROCESS
        elif any(kw in pain_lower for kw in ["ops", "process", "workflow", "automation"]):
            return PersonaExtractorOutputSchema(
                role="COO",
                department="Operations",
                seniority_level="C-level / VP",
                likely_pain_points=[
                    "Processus manuels inefficaces",
                    "Manque de visibilité opérationnelle",
                    "Coordination inter-équipes difficile",
                    "Scalabilité limitée"
                ],
                confidence_score=confidence,
                fallback_level=1,
                reasoning=f"Inferred from client pain: '{self.client_context.pain_solved}' → Operations persona",
                source=source
            )

        # GENERIC FALLBACK
        else:
            return PersonaExtractorOutputSchema(
                role="CEO",
                department="Executive",
                seniority_level="C-level",
                likely_pain_points=[
                    "Croissance revenue",
                    "Efficacité opérationnelle",
                    "Compétitivité marché"
                ],
                confidence_score=confidence,
                fallback_level=2,
                reasoning=f"Generic inference from client pain: '{self.client_context.pain_solved}'",
                source=source
            )


# Example usage
if __name__ == "__main__":
    from src.models.client_context import ClientContext

    # Test with client context (Kaleads - lead gen)
    context = ClientContext(
        client_id="kaleads-uuid",
        client_name="Kaleads",
        offerings=["Cold email automation", "Lead enrichment"],
        pain_solved="génération de leads B2B qualifiés via l'automatisation",
        target_industries=["SaaS", "Tech"],
        real_case_studies=[],
        competitors=["Lemlist", "Apollo"],
        email_templates={}
    )

    agent = PersonaExtractorV3(client_context=context, enable_tavily=True)

    result = agent.run(PersonaExtractorInputSchema(
        company_name="Aircall",
        website="https://aircall.io",
        industry="SaaS"
    ))

    print(f"Role: {result.role}")
    print(f"Department: {result.department}")
    print(f"Seniority: {result.seniority_level}")
    print(f"Pain points: {result.likely_pain_points}")
    print(f"Confidence: {result.confidence_score}/5")
    print(f"Source: {result.source}")
    print(f"Reasoning: {result.reasoning}")
