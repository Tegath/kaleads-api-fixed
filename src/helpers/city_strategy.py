"""
City Strategy - Intelligent scraping strategy based on population
Adapts scraping parameters based on city size to optimize cost/results
"""
import csv
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CityScrapingStrategy:
    """Strategy for scraping a specific city"""
    city_name: str
    department: str
    population: int
    max_pages: int
    priority: int  # 1=high, 2=medium, 3=low
    should_scrape: bool
    search_type: str  # 'comprehensive', 'moderate', 'light', 'skip'


class CityStrategyManager:
    """
    Manages intelligent scraping strategy based on city population.

    Strategy tiers:
    - Population > 100k: HIGH priority, max 10 pages (comprehensive)
    - Population 20k-100k: MEDIUM priority, max 5 pages (moderate)
    - Population 5k-20k: LOW priority, max 2 pages (light)
    - Population < 5k: SKIP (not cost-effective for most queries)

    Adjustable thresholds for different use cases.
    """

    def __init__(
        self,
        population_file: str = None,
        min_population: int = 5000,
        use_departments: bool = False
    ):
        """
        Initialize strategy manager.

        Args:
            population_file: Path to CSV with population data
            min_population: Minimum population to scrape (default 5000)
            use_departments: If True, group by department for large cities
        """
        self.min_population = min_population
        self.use_departments = use_departments
        self.cities_data = {}
        self.departments = {}

        if population_file:
            self._load_population_data(population_file)

    def _load_population_data(self, file_path: str):
        """Load population data from CSV"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    city_name = row.get('libgeo', '').strip()
                    department = row.get('dep', '').strip()
                    population = int(row.get('p21_pop', 0))

                    if city_name and population > 0:
                        self.cities_data[city_name] = {
                            'department': department,
                            'code_geo': row.get('codgeo', ''),
                            'population': population
                        }

                        # Track departments
                        if department not in self.departments:
                            self.departments[department] = []
                        self.departments[department].append(city_name)

            logger.info(f"Loaded {len(self.cities_data)} cities with population data")
            logger.info(f"Found {len(self.departments)} departments")

        except Exception as e:
            logger.error(f"Error loading population data: {e}")

    def get_city_strategy(self, city_name: str) -> CityScrapingStrategy:
        """
        Get scraping strategy for a specific city.

        Returns strategy with max_pages and priority based on population.
        """
        # Get city data
        city_data = self.cities_data.get(city_name, {})
        population = city_data.get('population', 0)
        department = city_data.get('department', 'Unknown')

        # Determine strategy based on population
        if population >= 100000:
            # Large cities: comprehensive scraping
            return CityScrapingStrategy(
                city_name=city_name,
                department=department,
                population=population,
                max_pages=10,
                priority=1,
                should_scrape=True,
                search_type='comprehensive'
            )

        elif population >= 20000:
            # Medium cities: moderate scraping
            return CityScrapingStrategy(
                city_name=city_name,
                department=department,
                population=population,
                max_pages=5,
                priority=2,
                should_scrape=True,
                search_type='moderate'
            )

        elif population >= self.min_population:
            # Small cities: light scraping
            return CityScrapingStrategy(
                city_name=city_name,
                department=department,
                population=population,
                max_pages=2,
                priority=3,
                should_scrape=True,
                search_type='light'
            )

        else:
            # Very small cities: skip
            return CityScrapingStrategy(
                city_name=city_name,
                department=department,
                population=population,
                max_pages=0,
                priority=4,
                should_scrape=False,
                search_type='skip'
            )

    def filter_cities_by_strategy(
        self,
        cities: List[str],
        min_priority: int = 3
    ) -> List[Dict]:
        """
        Filter and sort cities by strategy.

        Args:
            cities: List of city names
            min_priority: Include cities up to this priority (1-3)

        Returns:
            List of dicts with city + strategy
        """
        city_strategies = []

        for city in cities:
            strategy = self.get_city_strategy(city)

            # Filter by priority and should_scrape
            if strategy.should_scrape and strategy.priority <= min_priority:
                city_strategies.append({
                    'city': city,
                    'department': strategy.department,
                    'population': strategy.population,
                    'max_pages': strategy.max_pages,
                    'priority': strategy.priority,
                    'search_type': strategy.search_type
                })

        # Sort by priority (high first), then by population (large first)
        city_strategies.sort(key=lambda x: (x['priority'], -x['population']))

        logger.info(f"Filtered {len(cities)} cities → {len(city_strategies)} cities to scrape")
        logger.info(f"  Priority 1 (>100k): {sum(1 for c in city_strategies if c['priority'] == 1)}")
        logger.info(f"  Priority 2 (20k-100k): {sum(1 for c in city_strategies if c['priority'] == 2)}")
        logger.info(f"  Priority 3 (5k-20k): {sum(1 for c in city_strategies if c['priority'] == 3)}")

        return city_strategies

    def get_departments_for_large_cities(
        self,
        min_population: int = 100000
    ) -> List[str]:
        """
        Get unique departments containing large cities.

        For queries targeting large cities only, we can scrape by department
        instead of individual cities to reduce API calls.

        Example: Instead of "agence marketing Paris", "agence marketing Lyon"
                 Use: "agence marketing 75", "agence marketing 69"
        """
        large_city_departments = set()

        for city_name, data in self.cities_data.items():
            if data['population'] >= min_population:
                large_city_departments.add(data['department'])

        logger.info(f"Found {len(large_city_departments)} departments with cities > {min_population:,} inhabitants")
        return sorted(list(large_city_departments))

    def estimate_scraping_cost(
        self,
        cities_with_strategy: List[Dict],
        cost_per_page: float = 0.001
    ) -> Dict:
        """
        Estimate total cost and time for scraping.

        Args:
            cities_with_strategy: List from filter_cities_by_strategy()
            cost_per_page: Cost per API page (default RapidAPI ~$0.001)

        Returns:
            Dict with cost estimates
        """
        total_pages = sum(c['max_pages'] for c in cities_with_strategy)
        total_cities = len(cities_with_strategy)

        # Conservative estimate: 50% of max_pages will be used (intelligent pagination)
        actual_pages = int(total_pages * 0.5)

        # Estimate leads (avg 15 per page)
        estimated_leads = actual_pages * 15

        # Time estimate (0.5s per page + rate limiting)
        estimated_minutes = (actual_pages * 0.5) / 60

        return {
            'total_cities': total_cities,
            'total_pages_max': total_pages,
            'estimated_pages_used': actual_pages,
            'estimated_leads': estimated_leads,
            'estimated_cost_usd': round(actual_pages * cost_per_page, 2),
            'estimated_time_minutes': round(estimated_minutes, 1),
            'breakdown_by_priority': {
                'priority_1': len([c for c in cities_with_strategy if c['priority'] == 1]),
                'priority_2': len([c for c in cities_with_strategy if c['priority'] == 2]),
                'priority_3': len([c for c in cities_with_strategy if c['priority'] == 3])
            }
        }


# Global instance
_strategy_manager = None

def get_strategy_manager(
    population_file: str = None,
    min_population: int = 5000
) -> CityStrategyManager:
    """Get or create strategy manager singleton"""
    global _strategy_manager

    if _strategy_manager is None:
        # Try to find population file
        if population_file is None:
            base_path = Path(__file__).parent.parent.parent
            pop_file = base_path / "Population_villes_france.csv"
            if pop_file.exists():
                population_file = str(pop_file)

        _strategy_manager = CityStrategyManager(
            population_file=population_file,
            min_population=min_population
        )

    return _strategy_manager


if __name__ == "__main__":
    """Test city strategy"""
    import logging
    logging.basicConfig(level=logging.INFO)

    # Test with mock cities
    manager = get_strategy_manager(min_population=5000)

    test_cities = ["Paris", "Lyon", "Marseille", "Toulouse", "Nice",
                   "Nantes", "Strasbourg", "Montpellier", "Bordeaux",
                   "Lille", "Rennes", "Reims", "Le Havre", "Dijon"]

    # Get strategies
    strategies = manager.filter_cities_by_strategy(test_cities, min_priority=3)

    print("\n" + "="*60)
    print("City Scraping Strategies")
    print("="*60)

    for city_strat in strategies[:10]:
        print(f"{city_strat['city']:20} | Pop: {city_strat['population']:>7,} | "
              f"Max Pages: {city_strat['max_pages']} | Priority: {city_strat['priority']}")

    # Estimate cost
    cost_estimate = manager.estimate_scraping_cost(strategies)
    print("\n" + "="*60)
    print("Cost Estimate")
    print("="*60)
    print(f"Total cities: {cost_estimate['total_cities']}")
    print(f"Estimated leads: {cost_estimate['estimated_leads']:,}")
    print(f"Estimated cost: ${cost_estimate['estimated_cost_usd']}")
    print(f"Estimated time: {cost_estimate['estimated_time_minutes']} minutes")
