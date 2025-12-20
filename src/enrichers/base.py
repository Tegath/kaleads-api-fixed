"""
Base Enricher - Abstract interface for data enrichment sources.

All enrichers (Pappers, LinkedIn, Crunchbase, etc.) inherit from this.
This enables a pluggable architecture where new sources can be added easily.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import time


@dataclass
class EnrichmentResult:
    """Result from an enrichment operation."""
    source: str
    company_name: str
    data: Dict[str, Any]
    success: bool
    error: Optional[str] = None
    processing_time_ms: int = 0


class BaseEnricher(ABC):
    """
    Abstract base class for all enrichers.

    To add a new enrichment source:
    1. Create a new class inheriting from BaseEnricher
    2. Implement the abstract methods
    3. Register in the EnricherFactory

    Example:
        class MyCustomEnricher(BaseEnricher):
            def get_source_name(self) -> str:
                return "my_custom_source"

            def get_available_fields(self) -> List[str]:
                return ["field1", "field2"]

            def enrich(self, company_name: str, fields: List[str]) -> EnrichmentResult:
                # Fetch data from your source
                return EnrichmentResult(...)
    """

    @abstractmethod
    def get_source_name(self) -> str:
        """Return the name of this enrichment source."""
        pass

    @abstractmethod
    def get_available_fields(self) -> List[str]:
        """Return list of fields this enricher can fetch."""
        pass

    @abstractmethod
    def enrich(
        self,
        company_name: str,
        fields: Optional[List[str]] = None,
        **kwargs
    ) -> EnrichmentResult:
        """
        Fetch enrichment data for a company.

        Args:
            company_name: Name of the company to enrich
            fields: Specific fields to fetch (None = all available)
            **kwargs: Additional source-specific parameters

        Returns:
            EnrichmentResult with fetched data
        """
        pass

    def _timed_operation(self, operation_func, *args, **kwargs) -> tuple:
        """Helper to time an operation."""
        start = time.time()
        result = operation_func(*args, **kwargs)
        elapsed_ms = int((time.time() - start) * 1000)
        return result, elapsed_ms


class EnricherFactory:
    """
    Factory for creating enrichers.

    Enables dynamic enricher selection based on source name.

    Usage:
        factory = EnricherFactory()
        factory.register("pappers", PappersEnricher())
        factory.register("linkedin", LinkedInEnricher())

        enricher = factory.get("pappers")
        result = enricher.enrich("Company Name")
    """

    def __init__(self):
        self._enrichers: Dict[str, BaseEnricher] = {}

    def register(self, source_name: str, enricher: BaseEnricher):
        """Register an enricher for a source."""
        self._enrichers[source_name.lower()] = enricher

    def get(self, source_name: str) -> Optional[BaseEnricher]:
        """Get an enricher by source name."""
        return self._enrichers.get(source_name.lower())

    def list_sources(self) -> List[str]:
        """List all registered source names."""
        return list(self._enrichers.keys())

    def enrich_multi(
        self,
        company_name: str,
        sources: List[str],
        fields_per_source: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, EnrichmentResult]:
        """
        Enrich from multiple sources.

        Args:
            company_name: Company to enrich
            sources: List of source names to use
            fields_per_source: Optional dict mapping source -> fields

        Returns:
            Dict mapping source name -> EnrichmentResult
        """
        results = {}
        for source in sources:
            enricher = self.get(source)
            if enricher:
                fields = fields_per_source.get(source) if fields_per_source else None
                results[source] = enricher.enrich(company_name, fields)
            else:
                results[source] = EnrichmentResult(
                    source=source,
                    company_name=company_name,
                    data={},
                    success=False,
                    error=f"Unknown source: {source}"
                )
        return results


# Global factory instance
enricher_factory = EnricherFactory()
