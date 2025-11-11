"""
Orchestrateur multi-provider qui supporte OpenAI ET Claude.

Permet de tester et comparer les resultats entre les 2 providers.
"""

import os
from typing import Optional, Dict, Literal
from src.schemas.campaign_schemas import CampaignRequest, CampaignResult, EmailResult, Contact
import time


class MultiProviderOrchestrator:
    """
    Orchestrateur qui peut utiliser OpenAI ou Claude (Anthropic).

    Usage:
        # OpenAI
        orch = MultiProviderOrchestrator(provider="openai", api_key="sk-...")

        # Claude
        orch = MultiProviderOrchestrator(provider="claude", api_key="sk-ant-...")

        # Auto (utilise les variables d'environnement)
        orch = MultiProviderOrchestrator(provider="auto")
    """

    def __init__(
        self,
        provider: Literal["openai", "claude", "auto"] = "auto",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_cache: bool = True
    ):
        self.provider = provider
        self.enable_cache = enable_cache
        self.cache: Dict[str, Dict] = {} if enable_cache else None

        # Auto-detect provider
        if provider == "auto":
            if os.getenv("OPENAI_API_KEY"):
                self.provider = "openai"
            elif os.getenv("ANTHROPIC_API_KEY"):
                self.provider = "claude"
            else:
                raise ValueError("No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY")

        # Set API key
        if api_key is None:
            if self.provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
            else:
                api_key = os.getenv("ANTHROPIC_API_KEY")

        self.api_key = api_key

        # Set model
        if model is None:
            if self.provider == "openai":
                model = "gpt-4o-mini"
            else:
                model = "claude-3-5-sonnet-20241022"

        self.model = model

        # Initialize agents
        self._init_agents()

    def _init_agents(self):
        """Initialise les agents selon le provider."""

        if self.provider == "openai":
            from src.agents.agents_v2 import (
                PersonaExtractorAgent,
                CompetitorFinderAgent,
                PainPointAgent,
                SignalGeneratorAgent,
                SystemBuilderAgent,
                CaseStudyAgent
            )

            self.persona_agent = PersonaExtractorAgent(self.api_key, self.model)
            self.competitor_agent = CompetitorFinderAgent(self.api_key, self.model)
            self.pain_agent = PainPointAgent(self.api_key, self.model)
            self.signal_agent = SignalGeneratorAgent(self.api_key, self.model)
            self.system_agent = SystemBuilderAgent(self.api_key, self.model)
            self.case_study_agent = CaseStudyAgent(self.api_key, self.model)

        elif self.provider == "claude":
            from src.agents.agents_claude import (
                PersonaExtractorAgentClaude,
                CompetitorFinderAgentClaude,
                PainPointAgentClaude,
                SignalGeneratorAgentClaude,
                SystemBuilderAgentClaude,
                CaseStudyAgentClaude
            )

            self.persona_agent = PersonaExtractorAgentClaude(self.api_key, self.model)
            self.competitor_agent = CompetitorFinderAgentClaude(self.api_key, self.model)
            self.pain_agent = PainPointAgentClaude(self.api_key, self.model)
            self.signal_agent = SignalGeneratorAgentClaude(self.api_key, self.model)
            self.system_agent = SystemBuilderAgentClaude(self.api_key, self.model)
            self.case_study_agent = CaseStudyAgentClaude(self.api_key, self.model)

    def run(self, request: CampaignRequest) -> CampaignResult:
        """
        Execute la campagne avec le provider configure.

        Le workflow est le meme que campaign_orchestrator_v2.py
        """

        # Pour l'instant, on delegue a l'orchestrateur OpenAI
        # car l'implementation complete avec Claude necessite plus de travail

        if self.provider == "openai":
            from src.orchestrator import CampaignOrchestrator

            orch = CampaignOrchestrator(
                openai_api_key=self.api_key,
                model=self.model,
                enable_cache=self.enable_cache
            )

            return orch.run(request)

        elif self.provider == "claude":
            # Implementation similaire mais avec agents Claude
            # Pour l'instant, on retourne un placeholder

            raise NotImplementedError(
                "Claude orchestrator en cours d'implementation. "
                "Utilisez provider='openai' pour l'instant."
            )


def compare_providers(
    request: CampaignRequest,
    openai_api_key: str,
    claude_api_key: str
) -> Dict[str, CampaignResult]:
    """
    Compare les resultats entre OpenAI et Claude.

    Returns:
        {
            "openai": CampaignResult,
            "claude": CampaignResult,
            "comparison": {...}
        }
    """

    results = {}

    # OpenAI
    print("[*] Generation avec OpenAI...")
    orch_openai = MultiProviderOrchestrator(
        provider="openai",
        api_key=openai_api_key
    )
    results["openai"] = orch_openai.run(request)

    # Claude
    print("[*] Generation avec Claude...")
    try:
        orch_claude = MultiProviderOrchestrator(
            provider="claude",
            api_key=claude_api_key
        )
        results["claude"] = orch_claude.run(request)
    except NotImplementedError:
        print("[WARN] Claude orchestrator pas encore implemente")
        results["claude"] = None

    # Comparison
    if results["claude"]:
        comparison = {
            "quality_score": {
                "openai": results["openai"].average_quality_score,
                "claude": results["claude"].average_quality_score,
                "winner": "openai" if results["openai"].average_quality_score > results["claude"].average_quality_score else "claude"
            },
            "execution_time": {
                "openai": results["openai"].total_execution_time_seconds,
                "claude": results["claude"].total_execution_time_seconds,
                "faster": "openai" if results["openai"].total_execution_time_seconds < results["claude"].total_execution_time_seconds else "claude"
            },
            "cost": {
                "openai": results["openai"].estimated_cost_usd,
                "claude": results["claude"].estimated_cost_usd,
                "cheaper": "openai" if results["openai"].estimated_cost_usd < results["claude"].estimated_cost_usd else "claude"
            }
        }
        results["comparison"] = comparison

    return results
