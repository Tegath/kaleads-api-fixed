"""
Google Search Enricher - Web Search for Company Information.

Uses SerpAPI or Google Custom Search API to find:
- Recent news about the company
- Funding announcements
- Press releases
- Key personnel mentioned in articles
"""

import os
import requests
from typing import Dict, Any, List, Optional
from .base import BaseEnricher, EnrichmentResult, enricher_factory


class GoogleSearchEnricher(BaseEnricher):
    """
    Enricher using Google Search (via SerpAPI or Custom Search).

    Requires SERPAPI_KEY environment variable.

    Available fields:
    - recent_news: Recent news headlines
    - funding_news: Funding-related articles
    - leadership_news: CEO/leadership mentions
    - company_description: Description from search results
    """

    SERPAPI_URL = "https://serpapi.com/search"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SERPAPI_KEY")

    def get_source_name(self) -> str:
        return "google"

    def get_available_fields(self) -> List[str]:
        return [
            "recent_news",
            "funding_news",
            "leadership_news",
            "company_description",
            "website",
            "linkedin_url"
        ]

    def enrich(
        self,
        company_name: str,
        fields: Optional[List[str]] = None,
        **kwargs
    ) -> EnrichmentResult:
        """
        Search Google for company information.

        Args:
            company_name: Company name to search
            fields: Specific fields to fetch
            country: Country code for localized results (default: fr)
        """
        if not self.api_key:
            return EnrichmentResult(
                source="google",
                company_name=company_name,
                data={},
                success=False,
                error="SERPAPI_KEY not configured"
            )

        country = kwargs.get("country", "fr")

        try:
            data, elapsed = self._timed_operation(
                self._search_company, company_name, country
            )

            if not data:
                return EnrichmentResult(
                    source="google",
                    company_name=company_name,
                    data={},
                    success=False,
                    error="No results found",
                    processing_time_ms=elapsed
                )

            # Filter fields if specified
            if fields:
                data = {k: v for k, v in data.items() if k in fields}

            return EnrichmentResult(
                source="google",
                company_name=company_name,
                data=data,
                success=True,
                processing_time_ms=elapsed
            )

        except Exception as e:
            return EnrichmentResult(
                source="google",
                company_name=company_name,
                data={},
                success=False,
                error=str(e)
            )

    def _search_company(self, company_name: str, country: str) -> Dict[str, Any]:
        """Perform Google search for company."""
        result = {}

        # General company search
        general_response = self._serpapi_search(f"{company_name} entreprise", country)
        if general_response:
            result["company_description"] = self._extract_description(general_response)
            result["website"] = self._extract_website(general_response)
            result["linkedin_url"] = self._extract_linkedin(general_response)

        # News search
        news_response = self._serpapi_search(
            f"{company_name} actualites",
            country,
            search_type="news"
        )
        if news_response:
            result["recent_news"] = self._extract_news(news_response, limit=5)

        # Funding search
        funding_response = self._serpapi_search(
            f"{company_name} levee de fonds OR financement OR investissement",
            country,
            search_type="news"
        )
        if funding_response:
            result["funding_news"] = self._extract_news(funding_response, limit=3)

        return result

    def _serpapi_search(
        self,
        query: str,
        country: str,
        search_type: str = "search"
    ) -> Optional[Dict[str, Any]]:
        """Make SerpAPI request."""
        params = {
            "api_key": self.api_key,
            "q": query,
            "gl": country,
            "hl": "fr" if country == "fr" else "en",
            "num": 10
        }

        if search_type == "news":
            params["tbm"] = "nws"

        response = requests.get(self.SERPAPI_URL, params=params, timeout=15)
        response.raise_for_status()
        return response.json()

    def _extract_description(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract company description from knowledge graph or snippets."""
        # Try knowledge graph first
        kg = response.get("knowledge_graph", {})
        if kg.get("description"):
            return kg["description"]

        # Fallback to first organic result snippet
        organic = response.get("organic_results", [])
        if organic and organic[0].get("snippet"):
            return organic[0]["snippet"]

        return None

    def _extract_website(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract company website."""
        kg = response.get("knowledge_graph", {})
        if kg.get("website"):
            return kg["website"]

        # Try first organic result
        organic = response.get("organic_results", [])
        if organic:
            return organic[0].get("link")

        return None

    def _extract_linkedin(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract LinkedIn URL from results."""
        organic = response.get("organic_results", [])
        for result in organic:
            link = result.get("link", "")
            if "linkedin.com/company" in link:
                return link
        return None

    def _extract_news(
        self,
        response: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, str]]:
        """Extract news items from search results."""
        news_results = response.get("news_results", [])
        return [
            {
                "title": item.get("title"),
                "source": item.get("source"),
                "date": item.get("date"),
                "link": item.get("link"),
                "snippet": item.get("snippet")
            }
            for item in news_results[:limit]
        ]


# Register with factory
enricher_factory.register("google", GoogleSearchEnricher())
