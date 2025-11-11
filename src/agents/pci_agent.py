"""
PCI Filtering Agent - Filter contacts by Profil Client Ideal (ICP).

Ultra-cheap agent using DeepSeek or Gemini Flash.
Cost: ~$0.0001 per contact.
"""

import os
from typing import Optional
import instructor
import openai
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator, ChatHistory
from pydantic import Field

from src.providers.supabase_client import SupabaseClient, ClientContext


class PCIFilterInputSchema(BaseIOSchema):
    """
    Input for PCI filtering agent.

    Contains contact information to evaluate against client's ICP.
    """
    company_name: str = Field(..., description="Company name to evaluate")
    industry: str = Field(default="", description="Company industry/sector")
    employees: Optional[int] = Field(None, description="Number of employees")
    revenue: Optional[float] = Field(None, description="Annual revenue in USD")
    website: str = Field(default="", description="Company website")
    region: str = Field(default="", description="Geographic region")
    technologies: list[str] = Field(default_factory=list, description="Technologies used")

    # Context from Supabase
    client_pci: dict = Field(default_factory=dict, description="Client's PCI from Supabase")


class PCIFilterOutputSchema(BaseIOSchema):
    """
    Output from PCI filtering agent.

    Determines if contact matches Ideal Customer Profile.
    """
    match: bool = Field(..., description="True if contact matches ICP")
    score: float = Field(..., description="Match score 0-1")
    reason: str = Field(..., description="Explanation of match/no-match")
    recommended_action: str = Field(
        ...,
        description="Next action: 'PROCEED', 'SKIP', or 'MANUAL_REVIEW'"
    )

    # Metadata
    fallback_level: int = Field(default=0, description="Fallback level (0=perfect data)")
    confidence_score: int = Field(..., description="Confidence 0-100")


class PCIFilterAgent:
    """
    PCI Filtering Agent - Evaluate contacts against Ideal Customer Profile.

    Ultra-cheap model (DeepSeek/Gemini Flash): ~$0.0001 per contact.

    Usage:
        agent = PCIFilterAgent(api_key="sk-or-...")
        result = agent.run(contact_data, client_id="uuid-123")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek/deepseek-chat",
        use_openrouter: bool = True
    ):
        """
        Initialize PCI filtering agent.

        Args:
            api_key: OpenRouter or OpenAI API key
            model: Model to use (default: deepseek/deepseek-chat ultra-cheap)
            use_openrouter: If True, use OpenRouter endpoint
        """
        api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")

        # Configure client for OpenRouter or OpenAI
        if use_openrouter:
            client = instructor.from_openai(
                openai.OpenAI(
                    api_key=api_key,
                    base_url="https://openrouter.ai/api/v1"
                )
            )
        else:
            client = instructor.from_openai(openai.OpenAI(api_key=api_key))

        # System prompt
        system_prompt_generator = SystemPromptGenerator(
            background=[
                "You are a PCI (Profil Client Ideal) filtering expert.",
                "Your job is to evaluate if a contact matches the client's Ideal Customer Profile.",
                "You receive contact data and the client's PCI criteria.",
                "You must determine if this contact is worth pursuing.",
            ],
            steps=[
                "1. Review the client's PCI criteria (industry, company size, revenue, technologies, regions).",
                "2. Compare the contact's attributes against each PCI criterion.",
                "3. Calculate a match score (0-1) based on how many criteria are met.",
                "4. Provide a clear reason explaining the match or mismatch.",
                "5. Recommend an action: PROCEED (good match), SKIP (bad match), or MANUAL_REVIEW (uncertain).",
            ],
            output_instructions=[
                "Return JSON with match (bool), score (0-1), reason, and recommended_action.",
                "Score >= 0.7: match=True, action=PROCEED",
                "Score 0.4-0.7: match=False, action=MANUAL_REVIEW",
                "Score < 0.4: match=False, action=SKIP",
                "Be specific in your reason (e.g., 'Industry match, size too small, no tech stack data').",
                "Set confidence_score based on data quality (100 if all fields present, lower if missing).",
                "Set fallback_level: 0 if all data present, 1 if some missing, 2+ if critical data missing.",
            ],
        )

        config = AgentConfig(
            client=client,
            model=model,
            history=ChatHistory(),
            system_prompt_generator=system_prompt_generator,
        )

        self.agent = AtomicAgent[PCIFilterInputSchema, PCIFilterOutputSchema](config=config)
        self.supabase_client = SupabaseClient()

    def run(
        self,
        input_data: PCIFilterInputSchema,
        client_id: Optional[str] = None
    ) -> PCIFilterOutputSchema:
        """
        Run PCI filtering.

        Args:
            input_data: Contact information
            client_id: Client UUID to load PCI from Supabase

        Returns:
            PCIFilterOutputSchema with match decision
        """
        # Load PCI from Supabase if client_id provided
        if client_id:
            context = self.supabase_client.load_client_context(client_id)
            input_data.client_pci = context.pci.dict()

        return self.agent.run(user_input=input_data)

    def run_simple(
        self,
        company_name: str,
        industry: str = "",
        employees: Optional[int] = None,
        client_id: Optional[str] = None,
        **kwargs
    ) -> PCIFilterOutputSchema:
        """
        Simplified run method.

        Args:
            company_name: Company name
            industry: Industry/sector
            employees: Number of employees
            client_id: Client UUID for PCI loading
            **kwargs: Additional contact fields

        Returns:
            PCIFilterOutputSchema
        """
        input_data = PCIFilterInputSchema(
            company_name=company_name,
            industry=industry,
            employees=employees,
            **kwargs
        )

        return self.run(input_data, client_id)


def batch_filter_contacts(
    contacts: list[dict],
    client_id: str,
    api_key: Optional[str] = None
) -> list[dict]:
    """
    Batch filter multiple contacts.

    Best practice: Process in batches for efficiency.

    Args:
        contacts: List of contact dicts with company_name, industry, etc.
        client_id: Client UUID
        api_key: OpenRouter/OpenAI API key

    Returns:
        List of filtered contacts with PCI results

    Example:
        >>> contacts = [
        ...     {"company_name": "Aircall", "industry": "SaaS", "employees": 500},
        ...     {"company_name": "Local Bakery", "industry": "Food", "employees": 5}
        ... ]
        >>> filtered = batch_filter_contacts(contacts, "client-uuid")
        >>> good_matches = [c for c in filtered if c["pci_result"]["match"]]
    """
    agent = PCIFilterAgent(api_key=api_key)

    results = []
    for contact in contacts:
        input_data = PCIFilterInputSchema(
            company_name=contact.get("company_name", ""),
            industry=contact.get("industry", ""),
            employees=contact.get("employees"),
            revenue=contact.get("revenue"),
            website=contact.get("website", ""),
            region=contact.get("region", ""),
            technologies=contact.get("technologies", [])
        )

        result = agent.run(input_data, client_id=client_id)

        # Add result to contact
        contact_with_result = contact.copy()
        contact_with_result["pci_result"] = result.dict()

        results.append(contact_with_result)

    return results
