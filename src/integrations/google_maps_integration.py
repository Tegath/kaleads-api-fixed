"""
Google Maps Lead Generator Integration

Wrapper pour générer des leads depuis Google Maps via RapidAPI.
Cherche des entreprises locales dans plusieurs villes en parallèle.
"""

import requests
import time
import logging
from typing import List, Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

logger = logging.getLogger(__name__)


class GoogleMapsLeadGenerator:
    """
    Génère des leads depuis Google Maps via RapidAPI.

    Usage:
        generator = GoogleMapsLeadGenerator(api_key="your-rapidapi-key")
        leads = generator.search_multiple_cities(
            query="agence marketing",
            cities=["Paris", "Lyon", "Marseille"],
            max_results_per_city=50
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        host: str = "google-maps-extractor2.p.rapidapi.com"
    ):
        """
        Initialize Google Maps Lead Generator.

        Args:
            api_key: RapidAPI key (or use RAPIDAPI_KEY env var)
            host: RapidAPI host
        """
        self.api_key = api_key or os.getenv("RAPIDAPI_KEY")
        if not self.api_key:
            raise ValueError("RAPIDAPI_KEY not found in environment or constructor")

        self.host = host
        self.base_url = f"https://{host}"
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create session with automatic retry."""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host,
        }

    def search_places(
        self,
        query: str,
        location: str,
        page: int = 1,
        language: str = "fr"
    ) -> Optional[Dict]:
        """
        Search places on Google Maps.

        Args:
            query: Search keyword (e.g., "restaurants", "agence marketing")
            location: Location (e.g., "Paris 75001 France")
            page: Page number (for pagination)
            language: Language of results

        Returns:
            Dictionary with results or None on error
        """
        try:
            # Full search query
            search_query = f"{query} {location}"

            # Search endpoint (adapt according to actual API)
            endpoint = "/search"
            params = {
                "query": search_query,
                "page": page,
                "lang": language
            }

            logger.info(f"Searching: {search_query} (page {page})")

            response = self.session.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                params=params,
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            logger.info(f"Results found: {len(data.get('data', []))}")
            return data

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("API authentication error - Check your RapidAPI key")
            elif e.response.status_code == 429:
                logger.warning("Rate limit reached - Pausing before retry")
                time.sleep(5)
            else:
                logger.error(f"HTTP Error {e.response.status_code}: {e}")
            return None

        except Exception as e:
            logger.error(f"Error during search: {e}")
            return None

    def search_city_with_pagination(
        self,
        query: str,
        city: str,
        country: str = "France",
        max_results: int = None,
        language: str = "fr"
    ) -> List[Dict]:
        """
        Search a city with intelligent pagination (stops when no more results).

        Args:
            query: Search keyword
            city: City name
            country: Country name
            max_results: Maximum results (None = all results available)
            language: Language

        Returns:
            List of all results for this city
        """
        all_results = []
        page = 1
        location = f"{city} {country}"

        while True:
            # Check if we've reached max_results
            if max_results and len(all_results) >= max_results:
                logger.info(f"Reached max_results ({max_results}) for {city}")
                break

            # Search this page
            results = self.search_places(
                query=query,
                location=location,
                page=page,
                language=language
            )

            # No results or error = stop pagination
            if not results or "data" not in results:
                logger.info(f"No more results at page {page} for {city}")
                break

            page_results = results.get("data", [])

            # Empty page = stop pagination
            if not page_results:
                logger.info(f"Empty page {page} for {city} - stopping pagination")
                break

            # Add results
            for result in page_results:
                result["city"] = city
                result["country"] = country
                result["search_query"] = query
                result["source"] = "google_maps"

                # Normalize field names
                if "business_name" in result:
                    result["company_name"] = result["business_name"]
                elif "name" in result:
                    result["company_name"] = result["name"]

                all_results.append(result)

                # Stop if reached max
                if max_results and len(all_results) >= max_results:
                    break

            logger.info(f"Page {page}: Found {len(page_results)} results in {city} (total: {len(all_results)})")

            # Stop if we got fewer results than expected (likely last page)
            if len(page_results) < 10:  # Assuming 10-20 results per page
                logger.info(f"Page {page} has fewer results ({len(page_results)}) - likely last page")
                break

            # Rate limiting between pages
            time.sleep(0.3)
            page += 1

            # Safety: max 100 pages per city
            if page > 100:
                logger.warning(f"Reached max page limit (100) for {city}")
                break

        logger.info(f"✅ Completed {city}: {len(all_results)} total results across {page} pages")
        return all_results

    def search_multiple_cities(
        self,
        query: str,
        cities: List[str],
        max_results_per_city: int = 50,
        country: str = "France",
        use_pagination: bool = False
    ) -> List[Dict]:
        """
        Search the same keyword in multiple cities.

        Args:
            query: "agence marketing"
            cities: ["Paris", "Lyon", "Marseille"]
            max_results_per_city: 50 (ignored if use_pagination=True)
            country: "France" or "Belgique"
            use_pagination: If True, scrape ALL results with intelligent pagination

        Returns:
            List of leads with company_name, address, phone, website, etc.

        Example output:
            [
                {
                    "name": "Agence XYZ",
                    "address": "123 rue de Paris, 75001 Paris",
                    "phone": "+33 1 23 45 67 89",
                    "website": "https://agence-xyz.fr",
                    "rating": 4.5,
                    "reviews_count": 234,
                    "place_id": "ChIJ...",
                    "city": "Paris",
                    "search_query": "agence marketing",
                    "source": "google_maps"
                },
                ...
            ]
        """
        all_results = []
        seen_companies = set()  # Deduplication

        for idx, city in enumerate(cities, 1):
            logger.info(f"[{idx}/{len(cities)}] Searching '{query}' in {city}...")

            if use_pagination:
                # Use intelligent pagination (scrape all results)
                city_results = self.search_city_with_pagination(
                    query=query,
                    city=city,
                    country=country,
                    max_results=None,  # No limit
                    language="fr"
                )
            else:
                # Legacy mode: single page, limited results
                location = f"{city} {country}"
                results = self.search_places(
                    query=query,
                    location=location,
                    page=1,
                    language="fr"
                )

                if results and "data" in results:
                    city_results = results["data"][:max_results_per_city]

                    # Enrich with metadata
                    for result in city_results:
                        result["city"] = city
                        result["country"] = country
                        result["search_query"] = query
                        result["source"] = "google_maps"

                        # Normalize field names
                        if "business_name" in result:
                            result["company_name"] = result["business_name"]
                        elif "name" in result:
                            result["company_name"] = result["name"]
                else:
                    city_results = []

            # Deduplicate by company_name + city
            unique_city_results = []
            for result in city_results:
                company_key = f"{result.get('company_name', '').lower()}_{city.lower()}"
                if company_key not in seen_companies:
                    seen_companies.add(company_key)
                    unique_city_results.append(result)

            all_results.extend(unique_city_results)
            logger.info(f"✅ {city}: {len(unique_city_results)} unique results (total: {len(all_results)})")

            # Rate limiting between cities
            time.sleep(0.5)

        logger.info(f"🎯 Total unique results across all cities: {len(all_results)}")
        return all_results

    def search_all_cities_comprehensive(
        self,
        query: str,
        country: str = "France"
    ) -> List[Dict]:
        """
        Search ALL cities in France/Wallonie with intelligent pagination.
        Loads cities from CSV files and scrapes comprehensively.

        Args:
            query: "agence marketing"
            country: "France" or "Wallonie"

        Returns:
            List of ALL unique leads found across all cities
        """
        try:
            from ..helpers.cities_loader import get_cities_loader

            cities_loader = get_cities_loader()
            all_cities = cities_loader.get_all_cities(country=country)

            logger.info(f"🗺️  Starting comprehensive search: '{query}' in {len(all_cities)} cities ({country})")

            return self.search_multiple_cities(
                query=query,
                cities=all_cities,
                country=country,
                use_pagination=True  # Enable intelligent pagination
            )

        except Exception as e:
            logger.error(f"Error in comprehensive search: {e}")
            return []

    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """
        Get details for a specific place.

        Args:
            place_id: Google Maps place ID

        Returns:
            Dictionary with details or None
        """
        try:
            endpoint = "/place/details"
            params = {"place_id": place_id}

            response = self.session.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                params=params,
                timeout=30
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Error fetching place details: {e}")
            return None


if __name__ == "__main__":
    """Test Google Maps integration."""

    import logging
    logging.basicConfig(level=logging.INFO)

    # Test with mock or real API key
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        print("⚠️  RAPIDAPI_KEY not found in environment")
        print("Set it with: export RAPIDAPI_KEY=your-key")
        exit(1)

    generator = GoogleMapsLeadGenerator(api_key=api_key)

    print("="*60)
    print("🗺️  Testing Google Maps Lead Generator")
    print("="*60)

    # Test: Search agencies in 3 cities
    leads = generator.search_multiple_cities(
        query="agence marketing digital",
        cities=["Paris", "Lyon", "Marseille"],
        max_results_per_city=10
    )

    print(f"\n✅ Found {len(leads)} total leads")

    if leads:
        print(f"\n📊 Sample lead:")
        sample = leads[0]
        print(f"  - Company: {sample.get('company_name', 'N/A')}")
        print(f"  - City: {sample.get('city', 'N/A')}")
        print(f"  - Address: {sample.get('address', 'N/A')}")
        print(f"  - Phone: {sample.get('phone', 'N/A')}")
        print(f"  - Website: {sample.get('website', 'N/A')}")
        print(f"  - Rating: {sample.get('rating', 'N/A')}")

    print("\n" + "="*60)
