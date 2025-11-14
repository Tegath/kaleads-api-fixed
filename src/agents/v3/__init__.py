"""
v3.0 Agents - Context-Aware + Web-Enhanced

All v3 agents:
- Accept standardized ClientContext
- Use Tavily for web search (when appropriate)
- Have graceful fallback if web search unavailable
- Are generic and reusable across clients
"""

from src.agents.v3.competitor_finder_v3 import CompetitorFinderV3
from src.agents.v3.pain_point_analyzer_v3 import PainPointAnalyzerV3
from src.agents.v3.proof_generator_v3 import ProofGeneratorV3
from src.agents.v3.persona_extractor_v3 import PersonaExtractorV3
from src.agents.v3.signal_detector_v3 import SignalDetectorV3
from src.agents.v3.system_mapper_v3 import SystemMapperV3

__all__ = [
    "CompetitorFinderV3",
    "PainPointAnalyzerV3",
    "ProofGeneratorV3",
    "PersonaExtractorV3",
    "SignalDetectorV3",
    "SystemMapperV3",
]
