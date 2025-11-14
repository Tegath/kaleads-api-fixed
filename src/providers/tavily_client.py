"""
Tavily client for web search capabilities.

Tavily is an AI-powered search engine that provides agents with factual,
up-to-date information from the web.

Use cases:
- CompetitorFinder: Find competitors in a specific industry
- SignalDetector: Find recent news/events about a company
- SystemMapper: Find tech stack information
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime


class TavilyClient:
    """
    Wrapper for Tavily AI search API.

    This client provides a simple interface for agents to search the web
    and get factual, relevant information.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Tavily client.

        Args:
            api_key: Tavily API key (defaults to TAVILY_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.enabled = bool(self.api_key)

        if self.enabled:
            try:
                from tavily import TavilyClient as TavilySDK
                self.client = TavilySDK(api_key=self.api_key)
            except ImportError:
                print("Warning: tavily-python not installed. Run: pip install tavily-python")
                self.enabled = False
                self.client = None
        else:
            self.client = None
            print("Warning: TAVILY_API_KEY not found. Web search disabled.")

    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search the web using Tavily.

        Args:
            query: Search query (natural language)
            max_results: Maximum number of results to return (default: 5)
            search_depth: "basic" or "advanced" (default: "basic")
            include_domains: List of domains to include (e.g., ["linkedin.com"])
            exclude_domains: List of domains to exclude

        Returns:
            Dict with search results:
            {
                "query": "...",
                "results": [
                    {
                        "title": "...",
                        "url": "...",
                        "content": "...",
                        "score": 0.95
                    }
                ],
                "answer": "Direct answer to the query (if available)"
            }

        Example:
            >>> client = TavilyClient()
            >>> results = client.search("Who are the main competitors of Salesforce?")
            >>> print(results["answer"])
            "The main competitors of Salesforce include HubSpot, Microsoft Dynamics..."
        """
        if not self.enabled:
            return {
                "query": query,
                "results": [],
                "answer": "Web search disabled (Tavily not configured)",
                "error": "TAVILY_API_KEY not found"
            }

        try:
            # Call Tavily API
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_domains=include_domains,
                exclude_domains=exclude_domains
            )

            # Format response
            return {
                "query": query,
                "results": response.get("results", []),
                "answer": response.get("answer", ""),
                "search_depth": search_depth,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Tavily search error: {e}")
            return {
                "query": query,
                "results": [],
                "answer": "",
                "error": str(e)
            }

    def search_competitors(self, company_name: str, industry: str = "") -> List[str]:
        """
        Find competitors for a company.

        Args:
            company_name: Name of the company
            industry: Industry/sector (optional, improves results)

        Returns:
            List of competitor names

        Example:
            >>> client = TavilyClient()
            >>> competitors = client.search_competitors("Salesforce", "CRM")
            >>> print(competitors)
            ["HubSpot", "Microsoft Dynamics 365", "Zoho CRM"]
        """
        industry_str = f" in {industry}" if industry else ""
        query = f"Who are the main competitors of {company_name}{industry_str}?"

        results = self.search(query, max_results=3, search_depth="basic")

        # Extract competitor names from answer
        competitors = []
        answer = results.get("answer", "")

        if answer:
            # Simple extraction: look for common patterns
            # "competitors include X, Y, and Z"
            # "such as X, Y, Z"
            # "including X and Y"

            # Split by common separators
            for separator in [", and ", " and ", ", ", "include ", "such as ", "including "]:
                if separator in answer.lower():
                    parts = answer.split(separator)
                    for part in parts:
                        # Clean up and extract company names
                        cleaned = part.strip().strip(".,;")
                        if cleaned and len(cleaned) < 50:  # Reasonable company name length
                            competitors.append(cleaned)

        # Deduplicate and limit
        competitors = list(dict.fromkeys(competitors))[:5]

        return competitors if competitors else [f"Unknown (search: {company_name}{industry_str})"]

    def search_company_news(self, company_name: str, months: int = 3) -> List[Dict[str, str]]:
        """
        Find recent news about a company.

        Args:
            company_name: Name of the company
            months: How many months back to search (default: 3)

        Returns:
            List of news items:
            [
                {
                    "title": "...",
                    "url": "...",
                    "content": "...",
                    "date": "..."
                }
            ]

        Example:
            >>> client = TavilyClient()
            >>> news = client.search_company_news("Aircall")
            >>> for item in news:
            ...     print(f"{item['title']} - {item['date']}")
        """
        query = f"Recent news about {company_name} in the last {months} months"

        results = self.search(query, max_results=5, search_depth="basic")

        news_items = []
        for result in results.get("results", []):
            news_items.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "score": result.get("score", 0)
            })

        return news_items

    def search_tech_stack(self, company_name: str, website: str = "") -> List[str]:
        """
        Find technology stack used by a company.

        Args:
            company_name: Name of the company
            website: Company website (optional)

        Returns:
            List of technologies/tools

        Example:
            >>> client = TavilyClient()
            >>> tech = client.search_tech_stack("Aircall")
            >>> print(tech)
            ["Salesforce", "HubSpot", "AWS", "React"]
        """
        website_str = f" (website: {website})" if website else ""
        query = f"What technology stack and tools does {company_name}{website_str} use?"

        results = self.search(query, max_results=3, search_depth="basic")

        # Extract technologies from answer
        technologies = []
        answer = results.get("answer", "")

        if answer:
            # Simple extraction
            for separator in [", and ", " and ", ", ", "uses ", "including ", "such as "]:
                if separator in answer.lower():
                    parts = answer.split(separator)
                    for part in parts:
                        cleaned = part.strip().strip(".,;")
                        if cleaned and len(cleaned) < 40:
                            technologies.append(cleaned)

        # Deduplicate
        technologies = list(dict.fromkeys(technologies))[:8]

        return technologies if technologies else ["Unknown tech stack"]

    def quick_fact_check(self, statement: str) -> Dict[str, Any]:
        """
        Quick fact check for a statement.

        Useful for agents to verify information before using it.

        Args:
            statement: Statement to fact check

        Returns:
            Dict with verification:
            {
                "statement": "...",
                "verified": True/False,
                "confidence": 0.0-1.0,
                "explanation": "..."
            }

        Example:
            >>> client = TavilyClient()
            >>> result = client.quick_fact_check("Salesforce raised $5M in Series A in 2024")
            >>> if not result["verified"]:
            ...     print("This fact seems incorrect")
        """
        query = f"Is this statement accurate: {statement}"

        results = self.search(query, max_results=2, search_depth="basic")

        answer = results.get("answer", "").lower()

        # Simple verification based on answer
        verified = False
        confidence = 0.5

        if any(word in answer for word in ["yes", "correct", "true", "accurate"]):
            verified = True
            confidence = 0.8
        elif any(word in answer for word in ["no", "incorrect", "false", "inaccurate", "not"]):
            verified = False
            confidence = 0.8

        return {
            "statement": statement,
            "verified": verified,
            "confidence": confidence,
            "explanation": answer,
            "sources": [r.get("url") for r in results.get("results", [])]
        }


# Singleton instance
_tavily_client = None


def get_tavily_client() -> TavilyClient:
    """
    Get singleton Tavily client instance.

    Returns:
        TavilyClient instance
    """
    global _tavily_client
    if _tavily_client is None:
        _tavily_client = TavilyClient()
    return _tavily_client
