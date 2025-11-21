"""
PCI Qualifier Agent - Qualifies leads against Ideal Customer Profile
Uses LLM to analyze lead data and determine if it's a good fit
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PCIQualificationRequest(BaseModel):
    """Request model for PCI qualification"""
    company_name: str = Field(..., description="Company name")
    website: Optional[str] = Field(None, description="Company website URL")
    website_content: Optional[str] = Field(None, description="Scraped website content")
    city: Optional[str] = Field(None, description="Company city")
    country: Optional[str] = Field(default="France", description="Company country")
    rating: Optional[float] = Field(None, description="Google Maps rating")
    reviews_count: Optional[int] = Field(None, description="Number of reviews")
    phone: Optional[str] = Field(None, description="Phone number")
    client_id: str = Field(default="kaleads", description="Client ID for PCI matching")


class PCIQualificationResult(BaseModel):
    """Result of PCI qualification"""
    score: int = Field(..., description="Match score 0-100")
    stage: str = Field(..., description="Qualification stage")
    match: bool = Field(..., description="Whether lead matches PCI")
    reasons: List[str] = Field(..., description="Reasons for score")
    recommended_action: str = Field(..., description="Next action to take")
    tech_stack: Optional[List[str]] = Field(None, description="Detected technologies")
    estimated_company_size: Optional[str] = Field(None, description="Estimated company size")
    industry_match: Optional[bool] = Field(None, description="Industry matches PCI")


class PCIQualifierAgent:
    """
    Agent that qualifies leads against client's Ideal Customer Profile (ICP/PCI).

    Uses LLM to analyze:
    - Website content
    - Company info
    - Tech stack
    - Industry signals

    Returns a score 0-100 and qualification stage.
    """

    def __init__(self, client_id: str = "kaleads"):
        self.client_id = client_id

        # Load client PCI from Supabase
        from src.providers.supabase_client import SupabaseClient
        self.supabase_client = SupabaseClient()

        try:
            self.client_context = self.supabase_client.load_client_context_v3(client_id)
            logger.info(f"Loaded PCI for client: {self.client_context.client_name}")
        except Exception as e:
            logger.warning(f"Could not load client context v3, using v2: {e}")
            self.client_context = self.supabase_client.load_client_context(client_id)

    def qualify(self, request: PCIQualificationRequest) -> PCIQualificationResult:
        """
        Qualify a lead against the client's PCI.

        Args:
            request: Lead information to qualify

        Returns:
            PCIQualificationResult with score and reasons
        """
        logger.info(f"Qualifying lead: {request.company_name}")

        # Initialize result
        score = 0
        reasons = []
        tech_stack = []
        estimated_size = None
        industry_match = False

        # 1. Check if website exists (basic requirement)
        if not request.website:
            return PCIQualificationResult(
                score=0,
                stage="no_site",
                match=False,
                reasons=["No website found - cannot qualify"],
                recommended_action="skip",
                tech_stack=None,
                estimated_company_size=None,
                industry_match=False
            )

        # 2. Analyze website content if available
        if request.website_content:
            analysis = self._analyze_website_content(request.website_content)
            tech_stack = analysis.get("tech_stack", [])
            estimated_size = analysis.get("company_size", "unknown")
            keywords = analysis.get("keywords", [])

            # Score based on tech stack
            if tech_stack:
                score += 20
                reasons.append(f"Tech stack detected: {', '.join(tech_stack[:3])}")

        # 3. Check industry match using LLM
        if request.website_content and hasattr(self.client_context, 'target_industries'):
            target_industries = self.client_context.target_industries
            if target_industries:
                industry_match = self._check_industry_match(
                    request.website_content,
                    target_industries
                )
                if industry_match:
                    score += 30
                    reasons.append(f"Industry match: {', '.join(target_industries[:2])}")
                else:
                    reasons.append("Industry does not match target")

        # 4. Company size estimation
        size_score = self._score_company_size(estimated_size)
        score += size_score
        if size_score > 0:
            reasons.append(f"Company size: {estimated_size}")

        # 5. Rating quality (if available)
        if request.rating:
            if request.rating >= 4.0:
                score += 10
                reasons.append(f"High rating: {request.rating}/5")
            elif request.rating < 3.0:
                score -= 10
                reasons.append(f"Low rating: {request.rating}/5")

        # 6. Reviews volume (indicates active business)
        if request.reviews_count:
            if request.reviews_count > 50:
                score += 10
                reasons.append(f"Many reviews: {request.reviews_count}")
            elif request.reviews_count < 5:
                score -= 5
                reasons.append("Very few reviews")

        # 7. Website quality (basic check)
        if request.website_content:
            if len(request.website_content) > 2000:
                score += 10
                reasons.append("Substantial website content")

        # Normalize score to 0-100
        score = max(0, min(100, score))

        # Determine stage and action
        if score >= 70:
            stage = "qualified_high"
            match = True
            action = "enrich"
        elif score >= 50:
            stage = "qualified_medium"
            match = True
            action = "watch"
        elif score >= 30:
            stage = "qualified_low"
            match = False
            action = "skip"
        else:
            stage = "disqualified"
            match = False
            action = "skip"

        return PCIQualificationResult(
            score=score,
            stage=stage,
            match=match,
            reasons=reasons,
            recommended_action=action,
            tech_stack=tech_stack if tech_stack else None,
            estimated_company_size=estimated_size,
            industry_match=industry_match
        )

    def _analyze_website_content(self, content: str) -> Dict:
        """
        Analyze website content to extract tech stack, company size, keywords.

        Uses simple heuristics for now, can be replaced with LLM call.
        """
        content_lower = content.lower()

        # Detect tech stack (basic detection)
        tech_stack = []
        tech_keywords = {
            "react": "React",
            "vue": "Vue.js",
            "angular": "Angular",
            "node.js": "Node.js",
            "python": "Python",
            "django": "Django",
            "rails": "Ruby on Rails",
            "wordpress": "WordPress",
            "shopify": "Shopify",
            "woocommerce": "WooCommerce",
            "stripe": "Stripe",
            "hubspot": "HubSpot",
            "salesforce": "Salesforce",
            "aws": "AWS",
            "azure": "Azure",
            "google cloud": "Google Cloud"
        }

        for keyword, tech_name in tech_keywords.items():
            if keyword in content_lower:
                tech_stack.append(tech_name)

        # Estimate company size (very basic)
        company_size = "unknown"
        if "équipe" in content_lower or "team" in content_lower:
            if any(word in content_lower for word in ["startup", "petite équipe", "small team"]):
                company_size = "1-10"
            elif any(word in content_lower for word in ["pme", "sme", "moyenne"]):
                company_size = "10-50"
            elif any(word in content_lower for word in ["grande entreprise", "enterprise", "500+"]):
                company_size = "200+"

        # Extract keywords
        keywords = []
        keyword_list = ["saas", "b2b", "automation", "digital", "marketing", "tech", "software"]
        for kw in keyword_list:
            if kw in content_lower:
                keywords.append(kw)

        return {
            "tech_stack": tech_stack,
            "company_size": company_size,
            "keywords": keywords
        }

    def _check_industry_match(self, content: str, target_industries: List[str]) -> bool:
        """
        Check if website content matches target industries.

        Simple keyword matching for now, can be replaced with LLM.
        """
        content_lower = content.lower()

        for industry in target_industries:
            industry_keywords = industry.lower().split()
            if any(keyword in content_lower for keyword in industry_keywords):
                return True

        return False

    def _score_company_size(self, estimated_size: str) -> int:
        """
        Score company size based on PCI target.

        For Kaleads, target is 10-200 employees (SMB/Mid-market).
        """
        size_scores = {
            "1-10": 5,
            "10-50": 15,
            "50-200": 20,
            "200+": 10,
            "unknown": 0
        }

        return size_scores.get(estimated_size, 0)
