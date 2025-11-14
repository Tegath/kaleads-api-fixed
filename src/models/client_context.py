"""
Client Context Models for v3.0 Architecture.

This module defines the standardized ClientContext model that all agents use
to adapt their behavior based on the client's business, offerings, and target audience.

Key Principle: Agents are generic and reusable. ClientContext provides the
variable that makes them specific to each client.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class CaseStudy(BaseModel):
    """
    A real case study from the client.

    This represents a success story that can be used as social proof in emails.

    Example:
        >>> cs = CaseStudy(
        ...     company="Salesforce France",
        ...     industry="SaaS",
        ...     result="augmenter son pipeline de 300% en 6 mois",
        ...     metric="300% pipeline increase",
        ...     persona="VP Sales"
        ... )
    """
    company: str = Field(..., description="Name of the company helped (ex: 'Salesforce France')")
    industry: str = Field(..., description="Industry sector (ex: 'SaaS', 'Finance', 'Healthcare')")
    result: str = Field(
        ...,
        description="Measurable result achieved (ex: 'augmenter son pipeline de 300%')"
    )
    metric: Optional[str] = Field(
        None,
        description="Quantified metric (ex: '300% pipeline increase', '500 leads/month')"
    )
    persona: Optional[str] = Field(
        None,
        description="Persona who was helped (ex: 'VP Sales', 'Head of Marketing')"
    )
    description: Optional[str] = Field(
        None,
        description="Detailed description of the case study (optional)"
    )

    def to_short_string(self) -> str:
        """
        Convert to short string format for email insertion.

        Returns:
            String like "Salesforce France à augmenter son pipeline de 300%"
        """
        return f"{self.company} à {self.result}"

    def to_detailed_string(self) -> str:
        """
        Convert to detailed string format with industry.

        Returns:
            String like "Salesforce France (SaaS) à augmenter son pipeline de 300% en 6 mois"
        """
        return f"{self.company} ({self.industry}) à {self.result}"


class TemplateContext(BaseModel):
    """
    Context and guidelines for an email template.

    This tells agents HOW to generate content for this template.

    Example:
        >>> ctx = TemplateContext(
        ...     intention="Cold outreach pour générer un meeting",
        ...     tone="Professionnel mais friendly",
        ...     approach="Signal-focused + Social proof",
        ...     style="Court (< 100 mots)",
        ...     dos=["Mentionner un signal factuel", "Utiliser une vraie case study"],
        ...     donts=["Pas de pitch produit", "Pas de superlatifs"]
        ... )
    """
    intention: str = Field(
        ...,
        description="What is the goal of this email? (ex: 'Generate a meeting', 'Get a reply')"
    )
    tone: str = Field(
        ...,
        description="What tone should the email have? (ex: 'Professional but friendly', 'Direct and factual')"
    )
    approach: str = Field(
        ...,
        description="What approach to take? (ex: 'Signal-focused + Social proof', 'Pain point empathy')"
    )
    style: str = Field(
        ...,
        description="What style characteristics? (ex: 'Short (< 100 words)', 'One CTA only')"
    )
    dos: List[str] = Field(
        default_factory=list,
        description="List of things agents SHOULD do (ex: 'Use factual signals', 'Include metrics')"
    )
    donts: List[str] = Field(
        default_factory=list,
        description="List of things agents should NOT do (ex: 'No product pitch', 'No superlatives')"
    )

    def to_prompt_string(self) -> str:
        """
        Convert to a formatted string for agent prompts.

        Returns:
            Multi-line string with all context information
        """
        dos_str = "\n".join([f"  ✅ {do}" for do in self.dos])
        donts_str = "\n".join([f"  ❌ {dont}" for dont in self.donts])

        return f"""
📧 EMAIL TEMPLATE CONTEXT:
- Intention: {self.intention}
- Tone: {self.tone}
- Approach: {self.approach}
- Style: {self.style}

DO:
{dos_str}

DON'T:
{donts_str}
""".strip()


class TemplateExample(BaseModel):
    """
    A perfect example email for a specific contact type.

    This shows agents what a high-quality output looks like.

    Example:
        >>> example = TemplateExample(
        ...     for_contact={"company_name": "Aircall", "first_name": "Sophie", "industry": "SaaS"},
        ...     perfect_email="Bonjour Sophie,\\n\\nJ'ai vu qu'Aircall recrute 3 commerciaux...",
        ...     why_it_works="Signal factuel + case study réelle + CTA simple"
        ... )
    """
    for_contact: Dict[str, Any] = Field(
        ...,
        description="Contact information for this example (company_name, first_name, industry, etc.)"
    )
    perfect_email: str = Field(
        ...,
        description="The perfect email for this contact (complete text)"
    )
    why_it_works: str = Field(
        ...,
        description="Explanation of why this email is good (key success factors)"
    )

    def to_prompt_string(self) -> str:
        """
        Convert to a formatted string for agent prompts.

        Returns:
            Multi-line string with example and explanation
        """
        contact_str = ", ".join([f"{k}: {v}" for k, v in self.for_contact.items()])

        return f"""
📨 EXAMPLE OF PERFECT EMAIL:
For a contact: {contact_str}

EMAIL:
{self.perfect_email}

WHY IT WORKS:
{self.why_it_works}
""".strip()


class ClientContext(BaseModel):
    """
    Standardized client context for v3.0 architecture.

    This context contains ALL information about the client who is prospecting,
    and allows agents to personalize their behavior without hardcoding logic.

    Key Principle:
    - Agents are GENERIC (not tied to a specific client)
    - ClientContext is SPECIFIC (contains all client info)
    - Injection of ClientContext into agents = Adaptive behavior

    Example:
        >>> context = ClientContext(
        ...     client_id="kaleads-uuid",
        ...     client_name="Kaleads",
        ...     offerings=["lead generation B2B", "prospecting automation"],
        ...     pain_solved="génération de leads B2B qualifiés",
        ...     target_industries=["SaaS", "Consulting"],
        ...     real_case_studies=[
        ...         CaseStudy(
        ...             company="Salesforce France",
        ...             industry="SaaS",
        ...             result="augmenter son pipeline de 300%"
        ...         )
        ...     ]
        ... )
        >>> agent = PainPointAgent(client_context=context)
    """

    # ============================================
    # Identity
    # ============================================

    client_id: str = Field(
        ...,
        description="UUID of the client in Supabase"
    )

    client_name: str = Field(
        ...,
        description="Name of the client company (ex: 'Kaleads', 'TalentHub')"
    )

    # ============================================
    # Offerings (What the client sells)
    # ============================================

    offerings: List[str] = Field(
        default_factory=list,
        description="""
        List of the client's offerings/services.
        Ex: ['lead generation B2B', 'prospecting automation', 'data enrichment']
        """
    )

    personas: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="""
        List of target personas (raw format from Supabase).
        Each persona dict can contain: title, description, pain_point_solved, etc.
        """
    )

    # ============================================
    # Value Proposition
    # ============================================

    pain_solved: str = Field(
        default="",
        description="""
        What problem does the client solve?
        Ex: 'génération de leads B2B qualifiés via l'automatisation'

        This is CRITICAL for PainPointAgent to know what type of pain points to look for.
        """
    )

    value_proposition: str = Field(
        default="",
        description="The client's value proposition (optional, can be derived from pain_solved)"
    )

    # ============================================
    # ICP (Ideal Customer Profile)
    # ============================================

    target_industries: List[str] = Field(
        default_factory=list,
        description="""
        Industries the client targets.
        Ex: ['SaaS', 'Consulting', 'Agencies', 'Tech']
        """
    )

    target_company_sizes: List[str] = Field(
        default_factory=list,
        description="""
        Company sizes the client targets.
        Ex: ['10-50', '50-200', '200-1000']
        """
    )

    target_regions: List[str] = Field(
        default_factory=list,
        description="""
        Geographic regions the client targets.
        Ex: ['France', 'Europe', 'North America']
        """
    )

    # ============================================
    # Social Proof
    # ============================================

    real_case_studies: List[CaseStudy] = Field(
        default_factory=list,
        description="""
        Real case studies from the client.
        These are used by ProofGenerator to generate social proof.

        Format: List of CaseStudy objects with company, industry, result, metric.
        """
    )

    testimonials: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="""
        Customer testimonials (optional).
        Format: [{"company": "X", "quote": "...", "author": "..."}]
        """
    )

    # ============================================
    # Competition
    # ============================================

    competitors: List[str] = Field(
        default_factory=list,
        description="""
        List of the client's competitors.
        This helps CompetitorFinder avoid suggesting the client as a competitor.
        Ex: ['HubSpot', 'Salesforce', 'Pipedrive']
        """
    )

    # ============================================
    # Templates
    # ============================================

    email_templates: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="""
        Email templates with their context and examples.
        Format: {
            "template_name": {
                "template_content": "Bonjour {{first_name}},...",
                "context": TemplateContext(...),
                "example": TemplateExample(...)
            }
        }
        """
    )

    # ============================================
    # Metadata
    # ============================================

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # ============================================
    # Utility Methods
    # ============================================

    def get_offerings_str(self, limit: int = 3, separator: str = ", ") -> str:
        """
        Get offerings as a formatted string.

        Args:
            limit: Maximum number of offerings to include
            separator: Separator between offerings

        Returns:
            String like "lead generation B2B, prospecting automation, data enrichment"

        Example:
            >>> context.get_offerings_str(limit=2)
            "lead generation B2B, prospecting automation"
        """
        if not self.offerings:
            return "nos solutions"

        limited = self.offerings[:limit]
        return separator.join(limited)

    def get_target_industries_str(self, separator: str = ", ") -> str:
        """
        Get target industries as a formatted string.

        Args:
            separator: Separator between industries

        Returns:
            String like "SaaS, Consulting, Agencies"
        """
        if not self.target_industries:
            return "B2B companies"

        return separator.join(self.target_industries)

    def has_real_case_studies(self) -> bool:
        """
        Check if the client has real case studies.

        Returns:
            True if at least one case study exists
        """
        return len(self.real_case_studies) > 0

    def find_case_study_by_industry(self, industry: str) -> Optional[CaseStudy]:
        """
        Find a case study for a specific industry.

        Args:
            industry: Industry to search for (ex: "SaaS", "Finance")

        Returns:
            CaseStudy if found, None otherwise

        Example:
            >>> cs = context.find_case_study_by_industry("SaaS")
            >>> if cs:
            ...     print(cs.to_short_string())
            "Salesforce France à augmenter son pipeline de 300%"
        """
        if not industry:
            return None

        industry_lower = industry.lower()

        # Exact match
        for cs in self.real_case_studies:
            if cs.industry.lower() == industry_lower:
                return cs

        # Partial match (contains)
        for cs in self.real_case_studies:
            if industry_lower in cs.industry.lower() or cs.industry.lower() in industry_lower:
                return cs

        return None

    def get_best_case_study(self, prospect_industry: Optional[str] = None) -> Optional[CaseStudy]:
        """
        Get the best case study for a prospect.

        Args:
            prospect_industry: Industry of the prospect (optional)

        Returns:
            Best matching case study, or first case study if no match, or None

        Logic:
        1. If prospect_industry provided, try to find exact or partial match
        2. Otherwise, return first case study
        3. If no case studies, return None
        """
        if not self.has_real_case_studies():
            return None

        # Try to find by industry
        if prospect_industry:
            cs = self.find_case_study_by_industry(prospect_industry)
            if cs:
                return cs

        # Fallback to first case study
        return self.real_case_studies[0]

    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific email template by name.

        Args:
            template_name: Name of the template

        Returns:
            Template dict with content, context, example, or None if not found
        """
        return self.email_templates.get(template_name)

    def to_context_prompt(self, include_case_studies: bool = True, include_competitors: bool = True) -> str:
        """
        Convert ClientContext to a formatted prompt string for agents.

        Args:
            include_case_studies: Include case studies in prompt
            include_competitors: Include competitors in prompt

        Returns:
            Multi-line formatted string with all relevant context

        Example:
            >>> print(context.to_context_prompt())
            🎯 CLIENT CONTEXT:
            - Client Name: Kaleads
            - What Client Sells: lead generation B2B, prospecting automation
            - Problem Client Solves: génération de leads B2B qualifiés
            - Target Industries: SaaS, Consulting, Agencies
            ...
        """
        lines = [
            "🎯 CLIENT CONTEXT:",
            f"- Client Name: {self.client_name}",
            f"- What Client Sells: {self.get_offerings_str()}",
            f"- Problem Client Solves: {self.pain_solved}",
            f"- Target Industries: {self.get_target_industries_str()}",
        ]

        if include_case_studies and self.has_real_case_studies():
            lines.append("")
            lines.append("📊 REAL CASE STUDIES:")
            for cs in self.real_case_studies:
                lines.append(f"  - {cs.to_detailed_string()}")

        if include_competitors and self.competitors:
            lines.append("")
            lines.append(f"⚠️ CLIENT'S COMPETITORS (do not suggest these): {', '.join(self.competitors)}")

        return "\n".join(lines)

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
