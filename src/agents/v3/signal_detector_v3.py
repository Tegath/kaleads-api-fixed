"""
SignalDetector Agent v3.0 - Context-Aware + Web-Enhanced

This agent detects buying signals from prospect activity.

Key improvements in v3:
- Accepts ClientContext to filter relevant signals
- Uses Tavily for news search (finds REAL signals)
- Graceful fallback if web search unavailable
- Generic and reusable across clients
"""

from typing import Optional, List, Literal
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


class SignalDetectorInputSchema(BaseModel):
    """Input schema for Signal Detector."""
    company_name: str = Field(..., description="Name of the prospect company")
    website: str = Field(..., description="Website URL")
    industry: str = Field(default="", description="Industry/sector")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn company page URL")
    website_content: str = Field(default="", description="Scraped content (optional)")


class SignalDetectorOutputSchema(BaseModel):
    """Output schema for Signal Detector."""
    signal_type: Literal["hiring", "funding", "expansion", "tech_change", "award", "leadership", "none"] = Field(
        ..., description="Type of signal detected"
    )
    signal_description: str = Field(..., description="Description of the signal")
    relevance_to_client: str = Field(..., description="Why this signal is relevant to the client")
    confidence_score: int = Field(..., description="Confidence score 1-5 (5=verified, 1=inferred)")
    fallback_level: int = Field(..., description="Fallback level 0-3 (0=best, 3=generic)")
    reasoning: str = Field(..., description="Reasoning for the signal detection")
    source: str = Field(default="inference", description="Source: 'web_search', 'site_scrape', 'inference'")
    signal_date: Optional[str] = Field(default=None, description="Date of signal (if known)")


class SignalDetectorV3:
    """
    v3.0 Signal Detector Agent.

    Detects buying signals from prospect activity.

    Usage:
        >>> from src.models.client_context import ClientContext
        >>> context = ClientContext(
        ...     client_id="kaleads-uuid",
        ...     client_name="Kaleads",
        ...     pain_solved="génération de leads B2B"
        ... )
        >>> agent = SignalDetectorV3(client_context=context, enable_tavily=True)
        >>> result = agent.run(SignalDetectorInputSchema(
        ...     company_name="Aircall",
        ...     website="https://aircall.io",
        ...     industry="SaaS"
        ... ))
        >>> print(result.signal_type)
        "hiring"
        >>> print(result.signal_description)
        "Aircall is hiring 3 new sales positions"
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
        Initialize SignalDetector v3.

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

    def run(self, input_data: SignalDetectorInputSchema) -> SignalDetectorOutputSchema:
        """
        Detect buying signals for the prospect.

        Strategy:
        1. Try Tavily news search (last 3 months) → HIGH confidence
        2. Try scraping prospect's website (news/blog) → MEDIUM confidence
        3. Try industry inference → LOW confidence
        4. No signal found → Return "none"

        Args:
            input_data: Prospect information

        Returns:
            SignalDetectorOutputSchema with signal info
        """
        # Strategy 1: Tavily news search
        if self.tavily and self.tavily.enabled:
            result = self._try_tavily_news_search(input_data)
            if result:
                return result

        # Strategy 2: Scrape prospect's website (news/blog)
        if self.enable_scraping and input_data.website_content:
            result = self._try_scrape_news(input_data)
            if result:
                return result

        # Strategy 3: Industry inference
        result = self._try_industry_inference(input_data)
        if result:
            return result

        # Strategy 4: No signal found
        return self._no_signal_found(input_data)

    def _try_tavily_news_search(self, input_data: SignalDetectorInputSchema) -> Optional[SignalDetectorOutputSchema]:
        """
        Try to find signals using Tavily news search.

        This is the BEST strategy - uses real-time news data.

        Returns:
            SignalDetectorOutputSchema if found, None otherwise
        """
        try:
            print(f"[SignalDetectorV3] Using Tavily to find signals for {input_data.company_name}")

            # Search for recent news
            news = self.tavily.search_company_news(
                company_name=input_data.company_name,
                months=3
            )

            if not news:
                print(f"[SignalDetectorV3] Tavily found no news")
                return None

            # Analyze news for signals
            for article in news:
                title = article.get("title", "").lower()
                content = article.get("content", "").lower()
                combined = f"{title} {content}"

                # HIRING signal
                if any(kw in combined for kw in ["hiring", "recrute", "job opening", "open position", "career"]):
                    return self._build_signal(
                        signal_type="hiring",
                        description=f"{input_data.company_name} a récemment publié des offres d'emploi",
                        input_data=input_data,
                        confidence=5,
                        source="web_search",
                        date=article.get("published_date")
                    )

                # FUNDING signal
                if any(kw in combined for kw in ["funding", "raise", "investment", "series", "financement"]):
                    return self._build_signal(
                        signal_type="funding",
                        description=f"{input_data.company_name} a récemment levé des fonds",
                        input_data=input_data,
                        confidence=5,
                        source="web_search",
                        date=article.get("published_date")
                    )

                # EXPANSION signal
                if any(kw in combined for kw in ["expansion", "growth", "new office", "scale", "croissance"]):
                    return self._build_signal(
                        signal_type="expansion",
                        description=f"{input_data.company_name} est en phase d'expansion",
                        input_data=input_data,
                        confidence=5,
                        source="web_search",
                        date=article.get("published_date")
                    )

                # TECH CHANGE signal
                if any(kw in combined for kw in ["new technology", "migration", "adopted", "tech stack", "platform"]):
                    return self._build_signal(
                        signal_type="tech_change",
                        description=f"{input_data.company_name} a récemment changé sa stack technologique",
                        input_data=input_data,
                        confidence=5,
                        source="web_search",
                        date=article.get("published_date")
                    )

                # AWARD signal
                if any(kw in combined for kw in ["award", "recognition", "prize", "winner", "prix", "récompense"]):
                    return self._build_signal(
                        signal_type="award",
                        description=f"{input_data.company_name} a récemment reçu une distinction",
                        input_data=input_data,
                        confidence=5,
                        source="web_search",
                        date=article.get("published_date")
                    )

                # LEADERSHIP signal
                if any(kw in combined for kw in ["new ceo", "new cto", "new cmo", "appointed", "joins as"]):
                    return self._build_signal(
                        signal_type="leadership",
                        description=f"{input_data.company_name} a récemment changé de direction",
                        input_data=input_data,
                        confidence=5,
                        source="web_search",
                        date=article.get("published_date")
                    )

            print(f"[SignalDetectorV3] Tavily found news but no relevant signals")
            return None

        except Exception as e:
            print(f"[SignalDetectorV3] Tavily search failed: {e}")
            return None

    def _try_scrape_news(self, input_data: SignalDetectorInputSchema) -> Optional[SignalDetectorOutputSchema]:
        """
        Try to extract signals from scraped website content.

        Looks for:
        - News/blog sections
        - Press releases
        - Career pages

        Returns:
            SignalDetectorOutputSchema if found, None otherwise
        """
        content = input_data.website_content.lower()

        # HIRING signal from career page
        if any(kw in content for kw in ["career", "job", "join our team", "we're hiring", "open position"]):
            return self._build_signal(
                signal_type="hiring",
                description=f"{input_data.company_name} recrute actuellement",
                input_data=input_data,
                confidence=4,
                source="site_scrape"
            )

        # EXPANSION signal
        if any(kw in content for kw in ["new office", "expansion", "growing team", "scaling"]):
            return self._build_signal(
                signal_type="expansion",
                description=f"{input_data.company_name} est en phase de croissance",
                input_data=input_data,
                confidence=3,
                source="site_scrape"
            )

        return None

    def _try_industry_inference(self, input_data: SignalDetectorInputSchema) -> Optional[SignalDetectorOutputSchema]:
        """
        Infer potential signal based on industry patterns.

        Returns:
            SignalDetectorOutputSchema with inferred signal
        """
        # Only use inference for high-growth industries
        industry_lower = input_data.industry.lower()

        if any(kw in industry_lower for kw in ["saas", "tech", "startup"]):
            # Tech companies often hire
            return self._build_signal(
                signal_type="hiring",
                description=f"Les entreprises {input_data.industry} recrutent généralement de manière active",
                input_data=input_data,
                confidence=2,
                source="inference"
            )

        return None

    def _no_signal_found(self, input_data: SignalDetectorInputSchema) -> SignalDetectorOutputSchema:
        """
        Return when no signal found.

        Returns:
            SignalDetectorOutputSchema with signal_type="none"
        """
        return SignalDetectorOutputSchema(
            signal_type="none",
            signal_description="Aucun signal d'achat détecté récemment",
            relevance_to_client="N/A",
            confidence_score=1,
            fallback_level=3,
            reasoning="No signals found via web search, scraping, or inference",
            source="inference"
        )

    def _build_signal(
        self,
        signal_type: str,
        description: str,
        input_data: SignalDetectorInputSchema,
        confidence: int,
        source: str,
        date: Optional[str] = None
    ) -> SignalDetectorOutputSchema:
        """
        Build signal output with relevance to client.

        Args:
            signal_type: Type of signal
            description: Signal description
            input_data: Prospect information
            confidence: Confidence score
            source: Source of signal
            date: Signal date (optional)

        Returns:
            SignalDetectorOutputSchema
        """
        # Determine relevance based on client context and signal type
        relevance = self._determine_relevance(signal_type, input_data)

        return SignalDetectorOutputSchema(
            signal_type=signal_type,
            signal_description=description,
            relevance_to_client=relevance,
            confidence_score=confidence,
            fallback_level=0 if confidence >= 4 else 1,
            reasoning=f"Detected {signal_type} signal from {source}",
            source=source,
            signal_date=date
        )

    def _determine_relevance(self, signal_type: str, input_data: SignalDetectorInputSchema) -> str:
        """
        Determine why this signal is relevant to the client.

        Args:
            signal_type: Type of signal
            input_data: Prospect information

        Returns:
            Relevance explanation
        """
        if not self.client_context:
            return "Signal indique une opportunité potentielle"

        pain_lower = self.client_context.pain_solved.lower()

        # HIRING signal relevance
        if signal_type == "hiring":
            if any(kw in pain_lower for kw in ["lead", "sales", "client acquisition"]):
                return "Le recrutement indique une phase de croissance → besoin de leads qualifiés"
            elif any(kw in pain_lower for kw in ["rh", "recruit", "talent"]):
                return "Le recrutement actif indique un besoin d'outils RH efficaces"
            else:
                return "Le recrutement indique une phase de croissance et d'investissement"

        # FUNDING signal relevance
        elif signal_type == "funding":
            if any(kw in pain_lower for kw in ["lead", "sales"]):
                return "La levée de fonds indique budget disponible pour outils de croissance"
            else:
                return "La levée de fonds indique capacité d'investissement dans de nouveaux outils"

        # EXPANSION signal relevance
        elif signal_type == "expansion":
            if any(kw in pain_lower for kw in ["lead", "sales"]):
                return "L'expansion nécessite plus de clients → besoin de lead gen"
            elif any(kw in pain_lower for kw in ["ops", "process"]):
                return "L'expansion nécessite des processus scalables"
            else:
                return "L'expansion indique besoin d'outils pour scaler"

        # TECH CHANGE signal relevance
        elif signal_type == "tech_change":
            if any(kw in pain_lower for kw in ["devops", "cloud", "infrastructure"]):
                return "Le changement tech indique ouverture à de nouvelles solutions"
            else:
                return "Le changement tech indique période de modernisation"

        # AWARD signal relevance
        elif signal_type == "award":
            return "La reconnaissance indique ambition de croissance et excellence"

        # LEADERSHIP signal relevance
        elif signal_type == "leadership":
            return "Un nouveau leadership signifie souvent de nouvelles priorités et budgets"

        else:
            return "Signal indique opportunité de contact"


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

    agent = SignalDetectorV3(client_context=context, enable_tavily=True)

    result = agent.run(SignalDetectorInputSchema(
        company_name="Aircall",
        website="https://aircall.io",
        industry="SaaS"
    ))

    print(f"Signal Type: {result.signal_type}")
    print(f"Description: {result.signal_description}")
    print(f"Relevance: {result.relevance_to_client}")
    print(f"Confidence: {result.confidence_score}/5")
    print(f"Source: {result.source}")
    print(f"Reasoning: {result.reasoning}")
