"""
Integrations with external lead generation services.
"""

from src.integrations.google_maps_integration import GoogleMapsLeadGenerator
from src.integrations.jobspy_integration import JobSpyLeadGenerator

__all__ = [
    "GoogleMapsLeadGenerator",
    "JobSpyLeadGenerator"
]
