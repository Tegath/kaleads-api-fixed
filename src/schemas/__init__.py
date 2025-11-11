"""
Schemas Pydantic pour la validation des inputs/outputs des agents.
"""

from .agent_schemas import (
    PersonaExtractorInput,
    PersonaExtractorOutput,
    CompetitorFinderInput,
    CompetitorFinderOutput,
    PainPointInput,
    PainPointOutput,
    SignalGeneratorInput,
    SignalGeneratorOutput,
    SystemBuilderInput,
    SystemBuilderOutput,
    CaseStudyInput,
    CaseStudyOutput,
)

from .campaign_schemas import (
    CampaignRequest,
    EmailResult,
    CampaignResult,
    Contact,
)

__all__ = [
    "PersonaExtractorInput",
    "PersonaExtractorOutput",
    "CompetitorFinderInput",
    "CompetitorFinderOutput",
    "PainPointInput",
    "PainPointOutput",
    "SignalGeneratorInput",
    "SignalGeneratorOutput",
    "SystemBuilderInput",
    "SystemBuilderOutput",
    "CaseStudyInput",
    "CaseStudyOutput",
    "CampaignRequest",
    "EmailResult",
    "CampaignResult",
    "Contact",
]
