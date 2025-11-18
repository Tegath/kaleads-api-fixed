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

    def search_multiple_cities(
        self,
        query: str,
        cities: List[str],
        max_results_per_city: int = 50,
        country: str = "France"
    ) -> List[Dict]:
        """
        Search the same keyword in multiple cities.

        Args:
            query: "agence marketing"
            cities: ["Paris", "Lyon", "Marseille"]
            max_results_per_city: 50
            country: "France" or "Belgique"

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

        for city in cities:
            # Format: "agence marketing Paris France"
            location = f"{city} {country}"

            logger.info(f"Searching '{query}' in {city}...")

            results = self.search_places(
                query=query,
                location=location,
                page=1,
                language="fr"
            )

            if results and "data" in results:
                # Limit to first X results
                city_results = results["data"][:max_results_per_city]

                # Enrich with city and metadata
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

                all_results.extend(city_results)

                logger.info(f"Found {len(city_results)} results in {city}")

                # Rate limiting: pause between cities
                time.sleep(0.5)
            else:
                logger.warning(f"No results for '{query}' in {city}")

        logger.info(f"Total results across all cities: {len(all_results)}")
        return all_results

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
