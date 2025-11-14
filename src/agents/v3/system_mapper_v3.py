"""
SystemMapper Agent v3.0 - Context-Aware + Web-Enhanced

This agent maps the prospect's current tech stack.

Key improvements in v3:
- Accepts ClientContext to filter relevant technologies
- Uses Tavily for tech stack detection
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


class SystemMapperInputSchema(BaseModel):
    """Input schema for System Mapper."""
    company_name: str = Field(..., description="Name of the prospect company")
    website: str = Field(..., description="Website URL")
    industry: str = Field(default="", description="Industry/sector")
    product_category: str = Field(default="", description="Product category from PersonaExtractor")
    website_content: str = Field(default="", description="Scraped content (optional)")


class SystemMapperOutputSchema(BaseModel):
    """Output schema for System Mapper."""
    tech_stack: List[str] = Field(default_factory=list, description="List of technologies detected")
    relevant_tech: List[str] = Field(default_factory=list, description="Technologies relevant to client's offering")
    integration_opportunities: str = Field(default="", description="Integration opportunities description")
    confidence_score: int = Field(..., description="Confidence score 1-5 (5=verified, 1=inferred)")
    fallback_level: int = Field(..., description="Fallback level 0-3 (0=best, 3=generic)")
    reasoning: str = Field(..., description="Reasoning for the tech stack detection")
    source: str = Field(default="inference", description="Source: 'web_search', 'site_scrape', 'inference'")


class SystemMapperV3:
    """
    v3.0 System Mapper Agent.

    Maps prospect's current tech stack.

    Usage:
        >>> from src.models.client_context import ClientContext
        >>> context = ClientContext(
        ...     client_id="kaleads-uuid",
        ...     client_name="Kaleads",
        ...     pain_solved="génération de leads B2B"
        ... )
        >>> agent = SystemMapperV3(client_context=context, enable_tavily=True)
        >>> result = agent.run(SystemMapperInputSchema(
        ...     company_name="Aircall",
        ...     website="https://aircall.io",
        ...     industry="SaaS"
        ... ))
        >>> print(result.tech_stack)
        ["Salesforce", "HubSpot", "Intercom"]
        >>> print(result.relevant_tech)
        ["Salesforce", "HubSpot"]
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
        Initialize SystemMapper v3.

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

    def run(self, input_data: SystemMapperInputSchema) -> SystemMapperOutputSchema:
        """
        Map prospect's tech stack.

        Strategy:
        1. Try Tavily tech stack detection → HIGH confidence
        2. Try scraping prospect's website (integrations page) → MEDIUM confidence
        3. Try industry inference → LOW confidence
        4. Generic fallback → VERY LOW confidence

        Args:
            input_data: Prospect information

        Returns:
            SystemMapperOutputSchema with tech stack info
        """
        # Strategy 1: Tavily tech stack detection
        if self.tavily and self.tavily.enabled:
            result = self._try_tavily_tech_detection(input_data)
            if result:
                return result

        # Strategy 2: Scrape prospect's website (integrations page)
        if self.enable_scraping and input_data.website_content:
            result = self._try_scrape_tech(input_data)
            if result:
                return result

        # Strategy 3: Industry inference
        result = self._try_industry_inference(input_data)
        if result:
            return result

        # Strategy 4: Generic fallback
        return self._generic_fallback(input_data)

    def _try_tavily_tech_detection(self, input_data: SystemMapperInputSchema) -> Optional[SystemMapperOutputSchema]:
        """
        Try to detect tech stack using Tavily.

        This is the BEST strategy - uses real-time tech data.

        Returns:
            SystemMapperOutputSchema if found, None otherwise
        """
        try:
            print(f"[SystemMapperV3] Using Tavily to detect tech stack for {input_data.company_name}")

            # Search for tech stack
            tech_stack = self.tavily.search_tech_stack(
                company_name=input_data.company_name,
                website=input_data.website
            )

            if not tech_stack or tech_stack[0].startswith("Unknown"):
                print(f"[SystemMapperV3] Tavily found no tech stack")
                return None

            # Filter relevant tech based on client context
            relevant_tech = self._filter_relevant_tech(tech_stack, input_data)

            # Determine integration opportunities
            integration_opps = self._determine_integrations(relevant_tech, input_data)

            return SystemMapperOutputSchema(
                tech_stack=tech_stack,
                relevant_tech=relevant_tech,
                integration_opportunities=integration_opps,
                confidence_score=5,
                fallback_level=0,
                reasoning=f"Detected via Tavily tech stack search for '{input_data.company_name}'",
                source="web_search"
            )

        except Exception as e:
            print(f"[SystemMapperV3] Tavily tech detection failed: {e}")
            return None

    def _try_scrape_tech(self, input_data: SystemMapperInputSchema) -> Optional[SystemMapperOutputSchema]:
        """
        Try to extract tech stack from scraped website content.

        Looks for:
        - Integration pages
        - Tech stack mentions
        - Partner logos

        Returns:
            SystemMapperOutputSchema if found, None otherwise
        """
        content = input_data.website_content.lower()

        # Common patterns for integration pages
        integration_patterns = [
            "integrations",
            "partners",
            "works with",
            "compatible with",
            "tech stack"
        ]

        # Check if website has integration info
        has_integration_info = any(pattern in content for pattern in integration_patterns)

        if has_integration_info:
            # Found integration page - extract tech (simplified)
            # In real implementation, use LLM to extract specific tools
            tech_stack = self._extract_common_tools_from_content(content)

            if tech_stack:
                relevant_tech = self._filter_relevant_tech(tech_stack, input_data)
                integration_opps = self._determine_integrations(relevant_tech, input_data)

                return SystemMapperOutputSchema(
                    tech_stack=tech_stack,
                    relevant_tech=relevant_tech,
                    integration_opportunities=integration_opps,
                    confidence_score=4,
                    fallback_level=1,
                    reasoning="Extracted from website integrations page",
                    source="site_scrape"
                )

        return None

    def _try_industry_inference(self, input_data: SystemMapperInputSchema) -> Optional[SystemMapperOutputSchema]:
        """
        Infer tech stack based on industry patterns.

        Returns:
            SystemMapperOutputSchema with inferred tech
        """
        industry_lower = (input_data.industry or "").lower()
        category_lower = (input_data.product_category or "").lower()

        # Industry → Common tech stack mappings
        tech_mapping = {
            # SaaS companies
            "saas": ["Salesforce", "HubSpot", "Slack", "Google Workspace", "AWS"],
            "software": ["GitHub", "Jira", "Slack", "AWS", "Docker"],

            # E-commerce
            "ecommerce": ["Shopify", "Stripe", "Google Analytics", "Mailchimp"],
            "retail": ["Shopify", "WooCommerce", "Magento"],

            # Marketing
            "marketing": ["HubSpot", "Mailchimp", "Google Analytics", "Salesforce"],
            "advertising": ["Google Ads", "Facebook Ads", "HubSpot"],

            # Tech/DevOps
            "tech": ["AWS", "GitHub", "Docker", "Kubernetes", "Jenkins"],
            "devops": ["Jenkins", "GitLab", "Docker", "Kubernetes", "Terraform"],
            "cloud": ["AWS", "Azure", "Google Cloud", "Terraform"],

            # Finance
            "fintech": ["Stripe", "Plaid", "AWS", "Salesforce"],
            "finance": ["Salesforce", "NetSuite", "QuickBooks"],

            # HR
            "hr": ["Workday", "BambooHR", "Greenhouse", "Lever"],
            "recruitment": ["Greenhouse", "Lever", "LinkedIn Recruiter"],
        }

        # Find matching tech stack
        for keyword, tech_stack in tech_mapping.items():
            if keyword in industry_lower or keyword in category_lower:
                relevant_tech = self._filter_relevant_tech(tech_stack, input_data)
                integration_opps = self._determine_integrations(relevant_tech, input_data)

                return SystemMapperOutputSchema(
                    tech_stack=tech_stack,
                    relevant_tech=relevant_tech,
                    integration_opportunities=integration_opps,
                    confidence_score=3,
                    fallback_level=2,
                    reasoning=f"Inferred from industry '{input_data.industry}' and product category '{input_data.product_category}'",
                    source="inference"
                )

        return None

    def _generic_fallback(self, input_data: SystemMapperInputSchema) -> SystemMapperOutputSchema:
        """
        Generic fallback when no tech stack found.

        Returns generic tech stack.

        Returns:
            SystemMapperOutputSchema with generic fallback
        """
        # Generic tech stack
        generic_tech = ["CRM", "Email platform", "Analytics tool"]

        return SystemMapperOutputSchema(
            tech_stack=generic_tech,
            relevant_tech=[],
            integration_opportunities="Opportunités d'intégration à explorer lors de la conversation",
            confidence_score=1,
            fallback_level=3,
            reasoning="No specific tech stack found, using generic fallback",
            source="inference"
        )

    def _filter_relevant_tech(self, tech_stack: List[str], input_data: SystemMapperInputSchema) -> List[str]:
        """
        Filter tech stack for technologies relevant to client's offering.

        Args:
            tech_stack: Full tech stack
            input_data: Prospect information

        Returns:
            List of relevant technologies
        """
        if not self.client_context:
            return tech_stack

        pain_lower = self.client_context.pain_solved.lower()
        relevant = []

        for tech in tech_stack:
            tech_lower = tech.lower()

            # LEAD GEN / SALES
            if any(kw in pain_lower for kw in ["lead", "sales", "client acquisition"]):
                if any(kw in tech_lower for kw in ["crm", "salesforce", "hubspot", "pipedrive", "sales"]):
                    relevant.append(tech)

            # MARKETING
            elif any(kw in pain_lower for kw in ["marketing", "demand", "campaign"]):
                if any(kw in tech_lower for kw in ["marketing", "mailchimp", "hubspot", "marketo", "pardot"]):
                    relevant.append(tech)

            # HR / RECRUITMENT
            elif any(kw in pain_lower for kw in ["rh", "recruit", "talent"]):
                if any(kw in tech_lower for kw in ["hr", "workday", "bamboo", "greenhouse", "lever"]):
                    relevant.append(tech)

            # DEVOPS / INFRASTRUCTURE
            elif any(kw in pain_lower for kw in ["devops", "cloud", "infrastructure"]):
                if any(kw in tech_lower for kw in ["aws", "azure", "docker", "kubernetes", "jenkins", "terraform"]):
                    relevant.append(tech)

            # OPS / PROCESS
            elif any(kw in pain_lower for kw in ["ops", "process", "workflow"]):
                if any(kw in tech_lower for kw in ["slack", "asana", "jira", "monday", "workflow"]):
                    relevant.append(tech)

        return relevant

    def _determine_integrations(self, relevant_tech: List[str], input_data: SystemMapperInputSchema) -> str:
        """
        Determine integration opportunities based on relevant tech.

        Args:
            relevant_tech: List of relevant technologies
            input_data: Prospect information

        Returns:
            Integration opportunities description
        """
        if not relevant_tech:
            return "Opportunités d'intégration à explorer"

        if not self.client_context:
            return f"Intégration possible avec: {', '.join(relevant_tech)}"

        # Build context-aware integration description
        tech_list = ", ".join(relevant_tech[:3])  # Limit to 3

        pain_lower = self.client_context.pain_solved.lower()

        if any(kw in pain_lower for kw in ["lead", "sales"]):
            return f"Intégration native avec {tech_list} pour synchroniser les leads automatiquement"
        elif any(kw in pain_lower for kw in ["marketing"]):
            return f"Intégration avec {tech_list} pour automatiser les campagnes"
        elif any(kw in pain_lower for kw in ["rh", "recruit"]):
            return f"Intégration avec {tech_list} pour centraliser les données candidats"
        elif any(kw in pain_lower for kw in ["devops", "cloud"]):
            return f"Intégration avec {tech_list} pour automatiser les déploiements"
        else:
            return f"Intégration possible avec {tech_list}"

    def _extract_common_tools_from_content(self, content: str) -> List[str]:
        """
        Extract common tools from website content.

        Simplified extraction - in real implementation, use LLM.

        Args:
            content: Website content (lowercase)

        Returns:
            List of detected tools
        """
        common_tools = [
            "salesforce", "hubspot", "pipedrive", "zoho",
            "slack", "microsoft teams", "google workspace",
            "mailchimp", "marketo", "pardot",
            "aws", "azure", "google cloud",
            "github", "gitlab", "bitbucket",
            "docker", "kubernetes",
            "jira", "asana", "monday",
            "stripe", "paypal",
            "shopify", "woocommerce",
            "intercom", "zendesk", "freshdesk"
        ]

        detected = []
        for tool in common_tools:
            if tool.lower() in content:
                # Capitalize properly
                detected.append(tool.title())

        return detected


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

    agent = SystemMapperV3(client_context=context, enable_tavily=True)

    result = agent.run(SystemMapperInputSchema(
        company_name="Aircall",
        website="https://aircall.io",
        industry="SaaS",
        product_category="cloud phone solution"
    ))

    print(f"Tech Stack: {result.tech_stack}")
    print(f"Relevant Tech: {result.relevant_tech}")
    print(f"Integration Opportunities: {result.integration_opportunities}")
    print(f"Confidence: {result.confidence_score}/5")
    print(f"Source: {result.source}")
    print(f"Reasoning: {result.reasoning}")
