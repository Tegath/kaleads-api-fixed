"""
Cities Database Helper

Utilities for loading and using the cities database.
"""

import json
from pathlib import Path
from typing import List, Optional, Literal

# Path to cities database
CITIES_DB_PATH = Path(__file__).parent.parent.parent / "data" / "cities_database.json"


class CitiesHelper:
    """Helper for working with cities database."""

    def __init__(self):
        """Load cities database."""
        with open(CITIES_DB_PATH, "r", encoding="utf-8") as f:
            self.db = json.load(f)

    def get_cities(
        self,
        country: Literal["France", "Belgique"] = "France",
        strategy: Literal["top_10", "top_25", "all"] = "top_25"
    ) -> List[str]:
        """
        Get list of cities based on strategy.

        Args:
            country: "France" or "Belgique"
            strategy: "top_10", "top_25", or "all"

        Returns:
            List of city names

        Examples:
            >>> helper = CitiesHelper()
            >>> helper.get_cities("France", "top_10")
            ["Paris", "Marseille", "Lyon", ...]
        """
        if strategy == "all":
            if country == "France":
                return self.db["countries"]["France"]["top_50"]
            else:
                return self.db["countries"]["Belgique"]["top_20"]

        elif strategy in ["top_10", "top_25"]:
            return self.db["selection_strategies"][strategy].get(
                country.lower(),
                []
            )

        return []

    def get_tech_hubs(self) -> List[str]:
        """
        Get major tech hub cities (France + Belgique).

        Returns:
            List of tech hub cities
        """
        return self.db["selection_strategies"]["major_tech_hubs"]["cities"]

    def get_cities_by_region(
        self,
        country: Literal["France", "Belgique"],
        region: str
    ) -> List[str]:
        """
        Get cities in a specific region.

        Args:
            country: "France" or "Belgique"
            region: Region name (e.g., "Île-de-France", "Flandre")

        Returns:
            List of cities in that region

        Examples:
            >>> helper.get_cities_by_region("France", "Île-de-France")
            ["Paris", "Boulogne-Billancourt", "Versailles", ...]
        """
        regions = self.db["countries"][country].get("regions", {})
        return regions.get(region, [])

    def get_all_regions(self, country: Literal["France", "Belgique"]) -> List[str]:
        """
        Get list of all regions for a country.

        Args:
            country: "France" or "Belgique"

        Returns:
            List of region names
        """
        regions = self.db["countries"][country].get("regions", {})
        return list(regions.keys())

    def optimize_city_selection(
        self,
        target_count: int,
        pain_type: str,
        target_industries: List[str],
        country: Literal["France", "Belgique"] = "France"
    ) -> List[str]:
        """
        Smart city selection based on target count and context.

        Logic:
        - If local_services (restaurants, etc.) → All cities
        - If B2B tech → Tech hubs first
        - If general B2B → Top 25
        - Adjust count based on target_count

        Args:
            target_count: Number of leads desired
            pain_type: Type of pain solved
            target_industries: Industries targeted
            country: Country to focus on

        Returns:
            Optimized list of cities

        Examples:
            >>> helper.optimize_city_selection(500, "lead_generation", ["SaaS"], "France")
            ["Paris", "Lyon", "Toulouse", ...]  # Tech hubs + top cities
        """

        # Local services → All cities for maximum coverage
        if pain_type == "local_services":
            return self.get_cities(country, "all")

        # B2B Tech → Tech hubs first
        if any(ind in ["SaaS", "Tech", "Software", "IT"] for ind in target_industries):
            tech_hubs = self.get_tech_hubs()
            # Filter by country
            country_hubs = [
                city for city in tech_hubs
                if city in self.get_cities(country, "all")
            ]

            # If target_count is high, add more cities
            if target_count >= 500:
                top_25 = self.get_cities(country, "top_25")
                # Combine tech hubs + other top cities (deduplicated)
                combined = country_hubs + [c for c in top_25 if c not in country_hubs]
                return combined
            else:
                return country_hubs

        # General B2B → Top 10 or Top 25 based on target_count
        if target_count >= 300:
            return self.get_cities(country, "top_25")
        else:
            return self.get_cities(country, "top_10")


if __name__ == "__main__":
    """Test CitiesHelper."""

    helper = CitiesHelper()

    print("="*60)
    print("🗺️  Cities Database Helper")
    print("="*60)

    # Test 1: Get top 10 cities
    print("\n1️⃣ Top 10 cities in France:")
    top_10 = helper.get_cities("France", "top_10")
    print(f"   {', '.join(top_10)}")

    # Test 2: Get tech hubs
    print("\n2️⃣ Major tech hubs:")
    tech_hubs = helper.get_tech_hubs()
    print(f"   {', '.join(tech_hubs)}")

    # Test 3: Get cities by region
    print("\n3️⃣ Cities in Île-de-France:")
    idf = helper.get_cities_by_region("France", "Île-de-France")
    print(f"   {', '.join(idf)}")

    # Test 4: Optimize selection
    print("\n4️⃣ Optimized selection for SaaS lead gen (target: 500):")
    optimized = helper.optimize_city_selection(
        target_count=500,
        pain_type="lead_generation",
        target_industries=["SaaS", "Tech"],
        country="France"
    )
    print(f"   {len(optimized)} cities: {', '.join(optimized[:10])}...")

    # Test 5: Optimize for local services
    print("\n5️⃣ Optimized selection for local services (target: 1000):")
    optimized_local = helper.optimize_city_selection(
        target_count=1000,
        pain_type="local_services",
        target_industries=["Restaurant"],
        country="France"
    )
    print(f"   {len(optimized_local)} cities (all France)")

    print("\n" + "="*60)
