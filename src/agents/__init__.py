"""
Agents spécialisés pour la génération de variables d'emails (Atomic Agents v2).

Chaque agent est responsable d'une variable ou d'un ensemble de variables liées.
"""

# Import des agents v2
from .agents_v2 import (
    PersonaExtractorAgent,
    CompetitorFinderAgent,
    PainPointAgent,
    SignalGeneratorAgent,
    SystemBuilderAgent,
    CaseStudyAgent
)

__all__ = [
    "PersonaExtractorAgent",
    "CompetitorFinderAgent",
    "PainPointAgent",
    "SignalGeneratorAgent",
    "SystemBuilderAgent",
    "CaseStudyAgent",
]
