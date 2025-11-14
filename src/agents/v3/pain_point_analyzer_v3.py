"""
PainPointAnalyzer Agent v3.0 - Context-Aware + Adaptive

This agent identifies pain points that the prospect faces, in relation to what the CLIENT sells.

Key improvements in v3:
- Accepts ClientContext and adapts to client's business (lead gen, HR, tech, etc.)
- Automatically classifies pain type from client_context.pain_solved
- Generates instructions dynamically (no hardcoded Kaleads logic)
- Generic and reusable across all client types

Example:
    If client_context.pain_solved = "génération de leads B2B"
    → Agent will look for CLIENT ACQUISITION pain points

    If client_context.pain_solved = "recrutement et gestion RH"
    → Agent will look for HR/RECRUITMENT pain points
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field

try:
    from src.models.client_context import ClientContext
except ImportError:
    ClientContext = None


# ============================================
# Pain Type Classification
# ============================================

def classify_pain_type(pain_solved: str) -> Literal["client_acquisition", "hr_recruitment", "tech_infrastructure", "ops_efficiency", "marketing", "generic"]:
    """
    Classify the type of pain point based on what the client solves.

    Args:
        pain_solved: Description of the problem the client solves

    Returns:
        Pain type category

    Example:
        >>> classify_pain_type("génération de leads B2B qualifiés")
        "client_acquisition"
        >>> classify_pain_type("recrutement et gestion RH efficace")
        "hr_recruitment"
    """
    pain_lower = pain_solved.lower()

    # Client acquisition (lead gen, sales, prospecting)
    if any(kw in pain_lower for kw in ["lead", "prospect", "client", "sales", "pipeline", "commercial", "vente", "acquisition"]):
        return "client_acquisition"

    # HR/Recruitment
    elif any(kw in pain_lower for kw in ["rh", "recruit", "talent", "embauche", "hiring", "onboarding", "turnover"]):
        return "hr_recruitment"

    # Tech/Infrastructure
    elif any(kw in pain_lower for kw in ["devops", "cloud", "infrastructure", "deploy", "ci/cd", "tech", "scalable"]):
        return "tech_infrastructure"

    # Marketing
    elif any(kw in pain_lower for kw in ["marketing", "martech", "automation marketing", "génération de demande", "demand gen"]):
        return "marketing"

    # Ops/Efficiency
    elif any(kw in pain_lower for kw in ["ops", "efficiency", "efficacité", "process", "automation", "workflow", "productivité"]):
        return "ops_efficiency"

    else:
        return "generic"


# Pain type instructions
PAIN_TYPE_INSTRUCTIONS = {
    "client_acquisition": {
        "focus": "CLIENT ACQUISITION, LEAD GENERATION, SALES GROWTH, PROSPECTING",
        "good_examples": [
            "✅ 'difficulté à acquérir de nouveaux prospects qualifiés'",
            "✅ 'prospection manuelle qui consomme 15h par semaine'",
            "✅ 'taux de conversion faible des campagnes commerciales'",
            "✅ 'pipeline commercial insuffisant pour atteindre les objectifs'",
        ],
        "bad_examples": [
            "❌ 'processus RH inefficaces' (NOT related to client acquisition)",
            "❌ 'infrastructure technique obsolète' (NOT related to sales)",
            "❌ 'manque de candidats qualifiés' (THIS IS HR, NOT CLIENT ACQUISITION)",
        ],
        "context": "The prospect needs MORE CLIENTS/LEADS for their business. Focus on their ability to GET NEW CUSTOMERS."
    },
    "hr_recruitment": {
        "focus": "HR, RECRUITMENT, TALENT MANAGEMENT, ONBOARDING, RETENTION",
        "good_examples": [
            "✅ 'processus de recrutement manuel qui prend 3 semaines par poste'",
            "✅ 'difficulté à attirer des talents qualifiés'",
            "✅ 'taux de turnover élevé (30% par an)'",
            "✅ 'onboarding manuel qui consomme beaucoup de ressources'",
        ],
        "bad_examples": [
            "❌ 'difficulté à acquérir des clients' (NOT related to HR)",
            "❌ 'infrastructure cloud non scalable' (NOT related to HR)",
            "❌ 'prospection manuelle inefficace' (THIS IS SALES, NOT HR)",
        ],
        "context": "The prospect struggles with HIRING, MANAGING, or RETAINING employees. Focus on HR/talent challenges."
    },
    "tech_infrastructure": {
        "focus": "TECH INFRASTRUCTURE, DEVOPS, SCALABILITY, DEPLOYMENT, CI/CD",
        "good_examples": [
            "✅ 'déploiements manuels qui prennent 4h et génèrent des incidents'",
            "✅ 'infrastructure non scalable pour gérer la croissance'",
            "✅ 'pas de CI/CD, ce qui ralentit le time-to-market'",
            "✅ 'infrastructure cloud coûteuse et mal optimisée'",
        ],
        "bad_examples": [
            "❌ 'difficulté à recruter des développeurs' (THIS IS HR, NOT infrastructure)",
            "❌ 'manque de prospects qualifiés' (THIS IS SALES, NOT tech)",
            "❌ 'processus RH manuels' (NOT related to infrastructure)",
        ],
        "context": "The prospect has TECHNICAL/INFRASTRUCTURE challenges. Focus on deployment, scalability, DevOps."
    },
    "marketing": {
        "focus": "MARKETING AUTOMATION, DEMAND GENERATION, CAMPAIGN MANAGEMENT, LEAD NURTURING",
        "good_examples": [
            "✅ 'campagnes marketing manuelles qui prennent beaucoup de temps'",
            "✅ 'difficulté à mesurer le ROI des campagnes marketing'",
            "✅ 'lead nurturing manuel et inefficace'",
            "✅ 'pas d'automatisation des campagnes email'",
        ],
        "bad_examples": [
            "❌ 'prospection commerciale manuelle' (THIS IS SALES, NOT marketing)",
            "❌ 'processus RH inefficaces' (NOT related to marketing)",
        ],
        "context": "The prospect struggles with MARKETING automation, campaign management, or demand generation."
    },
    "ops_efficiency": {
        "focus": "OPERATIONAL EFFICIENCY, PROCESS AUTOMATION, WORKFLOW OPTIMIZATION, PRODUCTIVITY",
        "good_examples": [
            "✅ 'processus manuels qui consomment 20h par semaine'",
            "✅ 'pas d'automatisation, beaucoup de tâches répétitives'",
            "✅ 'workflows inefficaces qui ralentissent la productivité'",
            "✅ 'données dispersées dans plusieurs outils'",
        ],
        "bad_examples": [
            "❌ 'difficulté à acquérir des clients' (THIS IS SALES, NOT ops efficiency)",
            "❌ 'processus de recrutement long' (THIS IS HR, NOT ops)",
        ],
        "context": "The prospect has OPERATIONAL/PROCESS inefficiencies. Focus on automation, productivity, workflow."
    },
    "generic": {
        "focus": "BUSINESS CHALLENGES, GROWTH, EFFICIENCY, COMPETITIVENESS",
        "good_examples": [
            "✅ 'processus inefficaces qui limitent la croissance'",
            "✅ 'difficulté à scaler les opérations'",
            "✅ 'manque d'automatisation des processus métier'",
        ],
        "bad_examples": [],
        "context": "The prospect has general business challenges. Use broad, applicable pain points."
    },
}


# ============================================
# Schemas
# ============================================

class PainPointAnalyzerInputSchema(BaseModel):
    """Input schema for Pain Point Analyzer."""
    company_name: str = Field(..., description="Name of the prospect company")
    website: str = Field(..., description="Website URL")
    industry: str = Field(default="", description="Industry/sector")
    target_persona: str = Field(default="", description="Target persona from PersonaExtractor")
    product_category: str = Field(default="", description="Product category from PersonaExtractor")
    website_content: str = Field(default="", description="Scraped content (optional)")


class PainPointAnalyzerOutputSchema(BaseModel):
    """Output schema for Pain Point Analyzer."""
    problem_specific: str = Field(..., description="Specific pain point (lowercase fragment, no ending punctuation)")
    impact_measurable: str = Field(..., description="Measurable impact of the pain point")
    confidence_score: int = Field(..., description="Confidence score 1-5 (5=found on site, 1=inferred)")
    fallback_level: int = Field(..., description="Fallback level 0-3 (0=best, 3=generic)")
    reasoning: str = Field(..., description="Reasoning for the choice")
    pain_type: str = Field(..., description="Type of pain detected (client_acquisition, hr_recruitment, etc.)")


# ============================================
# Agent
# ============================================

class PainPointAnalyzerV3:
    """
    v3.0 Pain Point Analyzer Agent.

    Identifies pain points the prospect faces, adapted to what the CLIENT sells.

    Key feature: Automatically adapts to client type via ClientContext.

    Usage:
        >>> from src.models.client_context import ClientContext
        >>> # Lead gen client
        >>> context = ClientContext(
        ...     client_id="kaleads-uuid",
        ...     client_name="Kaleads",
        ...     pain_solved="génération de leads B2B qualifiés"
        ... )
        >>> agent = PainPointAnalyzerV3(client_context=context)
        >>> result = agent.run(PainPointAnalyzerInputSchema(
        ...     company_name="Aircall",
        ...     industry="SaaS"
        ... ))
        >>> print(result.problem_specific)
        "difficulté à acquérir suffisamment de prospects qualifiés"
        >>> print(result.pain_type)
        "client_acquisition"

        >>> # HR client
        >>> context_hr = ClientContext(
        ...     client_id="talenthub-uuid",
        ...     client_name="TalentHub",
        ...     pain_solved="recrutement et gestion RH efficace"
        ... )
        >>> agent_hr = PainPointAnalyzerV3(client_context=context_hr)
        >>> result_hr = agent_hr.run(PainPointAnalyzerInputSchema(
        ...     company_name="TechCorp",
        ...     industry="Tech"
        ... ))
        >>> print(result_hr.problem_specific)
        "processus de recrutement manuel qui prend plusieurs semaines"
        >>> print(result_hr.pain_type)
        "hr_recruitment"
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
        Initialize PainPointAnalyzer v3.

        Args:
            api_key: OpenRouter API key (optional)
            model: Model to use (optional)
            enable_scraping: Enable website scraping
            enable_tavily: Enable Tavily web search (currently unused by this agent, but kept for API consistency)
            client_context: Client context (RECOMMENDED - determines pain type)
        """
        self.api_key = api_key
        self.model = model
        self.enable_scraping = enable_scraping
        self.enable_tavily = enable_tavily  # Not used by PainPointAnalyzer, but kept for consistency
        self.client_context = client_context

        # Determine pain type from client context
        if client_context and client_context.pain_solved:
            self.pain_type = classify_pain_type(client_context.pain_solved)
            self.instructions = PAIN_TYPE_INSTRUCTIONS[self.pain_type]
        else:
            self.pain_type = "generic"
            self.instructions = PAIN_TYPE_INSTRUCTIONS["generic"]

        print(f"[PainPointAnalyzerV3] Initialized with pain_type: {self.pain_type}")

    def run(self, input_data: PainPointAnalyzerInputSchema) -> PainPointAnalyzerOutputSchema:
        """
        Identify pain points for the prospect.

        Strategy:
        1. Try to find pain point on scraped website
        2. Infer from industry + persona + client's pain_solved
        3. Generic fallback for the pain type

        Args:
            input_data: Prospect information

        Returns:
            PainPointAnalyzerOutputSchema with pain point info
        """
        # Strategy 1: Try scraping (if content provided)
        if self.enable_scraping and input_data.website_content:
            result = self._try_scrape_pain(input_data)
            if result:
                return result

        # Strategy 2: Infer from industry + persona + pain type
        result = self._infer_pain(input_data)
        if result:
            return result

        # Strategy 3: Generic fallback
        return self._generic_fallback(input_data)

    def _try_scrape_pain(self, input_data: PainPointAnalyzerInputSchema) -> Optional[PainPointAnalyzerOutputSchema]:
        """
        Try to extract pain point from scraped website content.

        This would require LLM analysis of the content.
        Placeholder for now.

        Returns:
            PainPointAnalyzerOutputSchema if found, None otherwise
        """
        # Placeholder - would use LLM to extract pain from website
        return None

    def _infer_pain(self, input_data: PainPointAnalyzerInputSchema) -> PainPointAnalyzerOutputSchema:
        """
        Infer pain point based on industry + persona + client's pain type.

        Uses pain type-specific mappings.

        Returns:
            PainPointAnalyzerOutputSchema with inferred pain
        """
        industry_lower = (input_data.industry or "").lower()
        persona_lower = (input_data.target_persona or "").lower()

        # Pain mappings by type
        if self.pain_type == "client_acquisition":
            pain = self._infer_client_acquisition_pain(industry_lower, persona_lower)
        elif self.pain_type == "hr_recruitment":
            pain = self._infer_hr_pain(industry_lower, persona_lower)
        elif self.pain_type == "tech_infrastructure":
            pain = self._infer_tech_pain(industry_lower, persona_lower)
        elif self.pain_type == "marketing":
            pain = self._infer_marketing_pain(industry_lower, persona_lower)
        elif self.pain_type == "ops_efficiency":
            pain = self._infer_ops_pain(industry_lower, persona_lower)
        else:
            pain = self._infer_generic_pain(industry_lower)

        return PainPointAnalyzerOutputSchema(
            problem_specific=pain["problem"],
            impact_measurable=pain["impact"],
            confidence_score=3,
            fallback_level=1,
            reasoning=f"Inferred from industry '{input_data.industry}' and pain type '{self.pain_type}'",
            pain_type=self.pain_type
        )

    def _infer_client_acquisition_pain(self, industry: str, persona: str) -> dict:
        """Infer CLIENT ACQUISITION pain points."""
        # SaaS/Tech
        if "saas" in industry or "software" in industry or "tech" in industry:
            return {
                "problem": "difficulté à générer suffisamment de leads qualifiés pour alimenter le pipeline commercial",
                "impact": "croissance ralentie et objectifs de vente non atteints"
            }
        # Consulting/Agencies
        elif "consult" in industry or "agency" in industry or "agence" in industry:
            return {
                "problem": "prospection manuelle qui consomme trop de temps et génère peu de résultats",
                "impact": "équipe commerciale surchargée et manque de nouveaux clients"
            }
        # Services
        elif "service" in industry:
            return {
                "problem": "taux de conversion faible des prospects en clients",
                "impact": "coût d'acquisition client élevé et rentabilité limitée"
            }
        # Generic
        else:
            return {
                "problem": "difficulté à acquérir de nouveaux clients de manière régulière et prévisible",
                "impact": "croissance incertaine et dépendance à quelques gros clients"
            }

    def _infer_hr_pain(self, industry: str, persona: str) -> dict:
        """Infer HR/RECRUITMENT pain points."""
        # Tech
        if "tech" in industry or "software" in industry or "saas" in industry:
            return {
                "problem": "processus de recrutement long qui prend plusieurs semaines par poste tech",
                "impact": "ralentissement du développement produit et perte de candidats qualifiés"
            }
        # Healthcare
        elif "health" in industry or "santé" in industry:
            return {
                "problem": "difficulté à attirer et retenir des professionnels de santé qualifiés",
                "impact": "taux de turnover élevé et coûts de recrutement importants"
            }
        # Retail
        elif "retail" in industry or "commerce" in industry:
            return {
                "problem": "turnover élevé qui nécessite des recrutements fréquents",
                "impact": "coûts de formation récurrents et qualité de service variable"
            }
        # Generic
        else:
            return {
                "problem": "processus de recrutement manuel qui consomme beaucoup de ressources RH",
                "impact": "time-to-hire élevé et difficulté à scaler l'équipe"
            }

    def _infer_tech_pain(self, industry: str, persona: str) -> dict:
        """Infer TECH/INFRASTRUCTURE pain points."""
        # SaaS/Tech
        if "saas" in industry or "tech" in industry or "software" in industry:
            return {
                "problem": "déploiements manuels qui prennent du temps et génèrent des incidents",
                "impact": "time-to-market ralenti et expérience utilisateur dégradée"
            }
        # E-commerce
        elif "commerce" in industry or "retail" in industry:
            return {
                "problem": "infrastructure non scalable lors des pics de trafic",
                "impact": "pertes de revenus lors des promotions et expérience client médiocre"
            }
        # FinTech
        elif "fin" in industry or "bank" in industry or "finance" in industry:
            return {
                "problem": "infrastructure legacy qui limite l'innovation et la rapidité",
                "impact": "difficulté à lancer de nouveaux produits et perte de compétitivité"
            }
        # Generic
        else:
            return {
                "problem": "infrastructure technique non optimisée qui ralentit les opérations",
                "impact": "coûts d'infrastructure élevés et agilité limitée"
            }

    def _infer_marketing_pain(self, industry: str, persona: str) -> dict:
        """Infer MARKETING pain points."""
        # SaaS/B2B
        if "saas" in industry or "b2b" in industry or "software" in industry:
            return {
                "problem": "campagnes marketing manuelles qui prennent beaucoup de temps à créer",
                "impact": "faible volume de leads et ROI marketing difficile à mesurer"
            }
        # E-commerce
        elif "commerce" in industry or "retail" in industry:
            return {
                "problem": "personnalisation limitée des campagnes marketing",
                "impact": "taux de conversion faible et coût d'acquisition client élevé"
            }
        # Generic
        else:
            return {
                "problem": "pas d'automatisation des campagnes marketing et du lead nurturing",
                "impact": "opportunités commerciales perdues et équipe marketing surchargée"
            }

    def _infer_ops_pain(self, industry: str, persona: str) -> dict:
        """Infer OPERATIONAL EFFICIENCY pain points."""
        return {
            "problem": "processus manuels et répétitifs qui consomment beaucoup de temps",
            "impact": "productivité limitée et erreurs fréquentes dans les opérations"
        }

    def _infer_generic_pain(self, industry: str) -> dict:
        """Infer GENERIC pain points."""
        return {
            "problem": "processus métier inefficaces qui limitent la croissance",
            "impact": "difficulté à scaler les opérations et compétitivité réduite"
        }

    def _generic_fallback(self, input_data: PainPointAnalyzerInputSchema) -> PainPointAnalyzerOutputSchema:
        """
        Generic fallback when no pain point found.

        Returns generic pain based on pain type.

        Returns:
            PainPointAnalyzerOutputSchema with generic fallback
        """
        fallback_pains = {
            "client_acquisition": {
                "problem": "difficulté à acquérir de nouveaux clients de manière prévisible",
                "impact": "croissance limitée et objectifs commerciaux difficiles à atteindre"
            },
            "hr_recruitment": {
                "problem": "processus de recrutement qui prend du temps et des ressources",
                "impact": "difficulté à trouver et retenir les bons talents"
            },
            "tech_infrastructure": {
                "problem": "infrastructure technique qui limite l'agilité et l'innovation",
                "impact": "coûts élevés et difficulté à s'adapter rapidement au marché"
            },
            "marketing": {
                "problem": "campagnes marketing manuelles et difficiles à mesurer",
                "impact": "ROI marketing incertain et génération de leads limitée"
            },
            "ops_efficiency": {
                "problem": "processus opérationnels manuels et peu efficaces",
                "impact": "productivité limitée et coûts opérationnels élevés"
            },
            "generic": {
                "problem": "processus métier inefficaces qui freinent la croissance",
                "impact": "difficulté à scaler et compétitivité réduite"
            }
        }

        pain = fallback_pains.get(self.pain_type, fallback_pains["generic"])

        return PainPointAnalyzerOutputSchema(
            problem_specific=pain["problem"],
            impact_measurable=pain["impact"],
            confidence_score=1,
            fallback_level=3,
            reasoning=f"Generic fallback for pain type '{self.pain_type}'",
            pain_type=self.pain_type
        )


# Example usage
if __name__ == "__main__":
    # Test with lead gen client
    print("=== Test 1: Lead Gen Client (Kaleads) ===")
    from src.models.client_context import ClientContext

    context = ClientContext(
        client_id="kaleads-uuid",
        client_name="Kaleads",
        offerings=["lead generation B2B"],
        pain_solved="génération de leads B2B qualifiés via l'automatisation"
    )

    agent = PainPointAnalyzerV3(client_context=context)

    result = agent.run(PainPointAnalyzerInputSchema(
        company_name="Aircall",
        industry="SaaS",
        target_persona="VP Sales"
    ))

    print(f"Pain type: {result.pain_type}")
    print(f"Problem: {result.problem_specific}")
    print(f"Impact: {result.impact_measurable}")
    print()

    # Test with HR client
    print("=== Test 2: HR Client (TalentHub) ===")
    context_hr = ClientContext(
        client_id="talenthub-uuid",
        client_name="TalentHub",
        offerings=["recrutement"],
        pain_solved="recrutement et gestion RH efficace"
    )

    agent_hr = PainPointAnalyzerV3(client_context=context_hr)

    result_hr = agent_hr.run(PainPointAnalyzerInputSchema(
        company_name="TechCorp",
        industry="Tech"
    ))

    print(f"Pain type: {result_hr.pain_type}")
    print(f"Problem: {result_hr.problem_specific}")
    print(f"Impact: {result_hr.impact_measurable}")
