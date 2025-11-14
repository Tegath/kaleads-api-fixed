"""
CompetitorFinder Agent v3.0 - Context-Aware + Web-Enhanced

This agent identifies competitors or similar tools used by the prospect.

Key improvements in v3:
- Accepts ClientContext (avoids suggesting client as competitor)
- Uses Tavily for web search (finds REAL competitors)
- Graceful fallback if web search unavailable
- Generic and reusable across clients
"""

from typing import Optional
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


class CompetitorFinderInputSchema(BaseModel):
    """Input schema for Competitor Finder."""
    company_name: str = Field(..., description="Name of the prospect company")
    website: str = Field(..., description="Website URL")
    industry: str = Field(default="", description="Industry/sector")
    product_category: str = Field(default="", description="Product category from PersonaExtractor")
    website_content: str = Field(default="", description="Scraped content (optional)")


class CompetitorFinderOutputSchema(BaseModel):
    """Output schema for Competitor Finder."""
    competitor_name: str = Field(..., description="Name of competitor/tool")
    competitor_product_category: str = Field(..., description="Category of competitor product")
    confidence_score: int = Field(..., description="Confidence score 1-5 (5=found on site, 1=guess)")
    fallback_level: int = Field(..., description="Fallback level 0-3 (0=best, 3=generic)")
    reasoning: str = Field(..., description="Reasoning for the choice")
    source: str = Field(default="inference", description="Source: 'web_search', 'site_scrape', 'inference'")


class CompetitorFinderV3:
    """
    v3.0 Competitor Finder Agent.

    Finds competitors or similar tools used by the prospect.

    Usage:
        >>> from src.models.client_context import ClientContext
        >>> context = ClientContext(
        ...     client_id="kaleads-uuid",
        ...     client_name="Kaleads",
        ...     competitors=["HubSpot", "Salesforce"]
        ... )
        >>> agent = CompetitorFinderV3(client_context=context, enable_tavily=True)
        >>> result = agent.run(CompetitorFinderInputSchema(
        ...     company_name="Aircall",
        ...     industry="SaaS",
        ...     product_category="cloud phone solution"
        ... ))
        >>> print(result.competitor_name)
        "Talkdesk"
        >>> print(result.source)
        "web_search"
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
        Initialize CompetitorFinder v3.

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

    def run(self, input_data: CompetitorFinderInputSchema) -> CompetitorFinderOutputSchema:
        """
        Find competitors for the prospect.

        Strategy:
        1. Try Tavily web search (if enabled) → HIGH confidence
        2. Try scraping prospect's website (if enabled) → MEDIUM confidence
        3. Try industry inference → LOW confidence
        4. Generic fallback → VERY LOW confidence

        Args:
            input_data: Prospect information

        Returns:
            CompetitorFinderOutputSchema with competitor info
        """
        # Strategy 1: Tavily web search
        if self.tavily and self.tavily.enabled:
            result = self._try_tavily_search(input_data)
            if result:
                return result

        # Strategy 2: Scrape prospect's website (looking for integrations, comparisons)
        if self.enable_scraping and input_data.website_content:
            result = self._try_scrape_competitor(input_data)
            if result:
                return result

        # Strategy 3: Industry inference
        result = self._try_industry_inference(input_data)
        if result:
            return result

        # Strategy 4: Generic fallback
        return self._generic_fallback(input_data)

    def _try_tavily_search(self, input_data: CompetitorFinderInputSchema) -> Optional[CompetitorFinderOutputSchema]:
        """
        Try to find competitors using Tavily web search.

        This is the BEST strategy - uses real-time web data.

        Returns:
            CompetitorFinderOutputSchema if found, None otherwise
        """
        try:
            print(f"[CompetitorFinderV3] Using Tavily to find competitors for {input_data.company_name}")

            # Search for competitors
            competitors = self.tavily.search_competitors(
                company_name=input_data.company_name,
                industry=input_data.industry or input_data.product_category
            )

            if not competitors or competitors[0].startswith("Unknown"):
                print(f"[CompetitorFinderV3] Tavily found no competitors")
                return None

            # Filter out our client if in results
            if self.client_context:
                competitors = [
                    c for c in competitors
                    if self.client_context.client_name.lower() not in c.lower()
                    and c.lower() not in [comp.lower() for comp in self.client_context.competitors]
                ]

            if not competitors:
                print(f"[CompetitorFinderV3] All competitors filtered out (were client or client's competitors)")
                return None

            # Take first competitor
            competitor = competitors[0]

            return CompetitorFinderOutputSchema(
                competitor_name=competitor,
                competitor_product_category=input_data.product_category or input_data.industry,
                confidence_score=5,
                fallback_level=0,
                reasoning=f"Found via Tavily web search for '{input_data.company_name}' competitors",
                source="web_search"
            )

        except Exception as e:
            print(f"[CompetitorFinderV3] Tavily search failed: {e}")
            return None

    def _try_scrape_competitor(self, input_data: CompetitorFinderInputSchema) -> Optional[CompetitorFinderOutputSchema]:
        """
        Try to extract competitor from scraped website content.

        Looks for mentions of competitors in:
        - Integration pages
        - Comparison pages
        - Case studies

        Returns:
            CompetitorFinderOutputSchema if found, None otherwise
        """
        # Simplified extraction - in real implementation, use LLM to extract
        content = input_data.website_content.lower()

        # Common patterns
        patterns = [
            "integrates with",
            "compatible with",
            "compared to",
            "alternative to",
            "replaces",
            "migrated from"
        ]

        # This is a placeholder - real implementation would use LLM
        # For now, just check if patterns exist
        for pattern in patterns:
            if pattern in content:
                # Found potential competitor mention
                # In real implementation, extract the actual name using LLM
                return None  # Placeholder

        return None

    def _try_industry_inference(self, input_data: CompetitorFinderInputSchema) -> Optional[CompetitorFinderOutputSchema]:
        """
        Infer competitor based on industry/product category.

        Uses industry knowledge to suggest likely competitors.

        Returns:
            CompetitorFinderOutputSchema with inferred competitor
        """
        industry_lower = (input_data.industry or "").lower()
        category_lower = (input_data.product_category or "").lower()

        # Industry → Competitor mappings
        competitor_mapping = {
            # CRM
            ("crm", "salesforce"): "HubSpot CRM",
            ("crm", "hubspot"): "Salesforce",
            ("crm", "pipedrive"): "HubSpot CRM",

            # Phone/Communication
            ("phone", "cloud phone"): "RingCentral",
            ("voip", "telephony"): "8x8",
            ("communication", "cloud call"): "Talkdesk",

            # Marketing Automation
            ("marketing automation", "email"): "Marketo",
            ("marketing", "automation"): "Pardot",

            # HR Tech
            ("hr", "recruitment"): "Greenhouse",
            ("talent", "recruiting"): "Lever",
            ("payroll", "hr"): "Gusto",

            # DevOps
            ("devops", "ci/cd"): "Jenkins",
            ("cloud", "infrastructure"): "Terraform",
            ("deployment", "automation"): "GitLab CI",

            # E-commerce
            ("ecommerce", "online store"): "Shopify",
            ("commerce", "marketplace"): "BigCommerce",

            # Analytics
            ("analytics", "data"): "Google Analytics",
            ("business intelligence", "bi"): "Tableau",

            # Project Management
            ("project management", "tasks"): "Asana",
            ("collaboration", "team"): "Monday.com",
        }

        # Try to find match
        for (key1, key2), competitor in competitor_mapping.items():
            if (key1 in industry_lower or key1 in category_lower) and \
               (key2 in industry_lower or key2 in category_lower):
                # Filter out client
                if self.client_context and \
                   (self.client_context.client_name.lower() in competitor.lower() or \
                    competitor.lower() in [c.lower() for c in self.client_context.competitors]):
                    continue

                return CompetitorFinderOutputSchema(
                    competitor_name=competitor,
                    competitor_product_category=input_data.product_category or input_data.industry,
                    confidence_score=3,
                    fallback_level=1,
                    reasoning=f"Inferred from industry '{input_data.industry}' and product category '{input_data.product_category}'",
                    source="inference"
                )

        return None

    def _generic_fallback(self, input_data: CompetitorFinderInputSchema) -> CompetitorFinderOutputSchema:
        """
        Generic fallback when no competitor found.

        Returns generic statement instead of guessing.

        Returns:
            CompetitorFinderOutputSchema with generic fallback
        """
        # Generic based on industry
        industry = input_data.industry or "leur secteur"

        if "saas" in industry.lower() or "software" in industry.lower():
            generic = "des solutions SaaS concurrentes"
        elif "tech" in industry.lower():
            generic = "d'autres technologies du marché"
        else:
            generic = "des solutions similaires du secteur"

        return CompetitorFinderOutputSchema(
            competitor_name=generic,
            competitor_product_category=input_data.product_category or industry,
            confidence_score=1,
            fallback_level=3,
            reasoning="No specific competitor found, using generic fallback",
            source="inference"
        )


# Example usage
if __name__ == "__main__":
    # Test with Tavily
    agent = CompetitorFinderV3(enable_tavily=True)

    result = agent.run(CompetitorFinderInputSchema(
        company_name="Aircall",
        industry="SaaS",
        product_category="cloud phone solution",
        website="https://aircall.io"
    ))

    print(f"Competitor: {result.competitor_name}")
    print(f"Confidence: {result.confidence_score}/5")
    print(f"Source: {result.source}")
    print(f"Reasoning: {result.reasoning}")
