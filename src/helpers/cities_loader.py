"""
Cities Loader - Load all cities from CSV files
Loads French and Belgian cities for comprehensive lead generation
"""
import csv
import os
from typing import List, Dict
from pathlib import Path


class CitiesLoader:
    """Load and manage cities from CSV files"""

    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.france_cities = []
        self.belgium_cities = []
        self.wallonie_cities = []
        self._load_cities()

    def _load_cities(self):
        """Load all cities from CSV files"""
        # Load French cities
        france_file = self.base_path / "Villes_france.csv"
        if france_file.exists():
            self.france_cities = self._load_france_csv(france_file)

        # Load Belgian cities
        belgium_file = self.base_path / "Villes_belgique.csv"
        if belgium_file.exists():
            all_belgium = self._load_belgium_csv(belgium_file)
            self.wallonie_cities = [c for c in all_belgium if c.get('region') == 'wallonie']
            self.belgium_cities = all_belgium

    def _load_france_csv(self, file_path: Path) -> List[str]:
        """Load French cities from CSV (ville name is column 3)"""
        cities = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip empty first line
                for row in reader:
                    if len(row) >= 3 and row[2]:
                        city_name = row[2].strip()
                        if city_name:
                            cities.append(city_name)
        except Exception as e:
            print(f"Error loading French cities: {e}")

        return cities

    def _load_belgium_csv(self, file_path: Path) -> List[Dict[str, str]]:
        """Load Belgian cities from CSV with region info"""
        cities = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    city_name = row.get('Ville', '').strip()
                    region = row.get('Région Belgique', '').strip().lower()
                    if city_name:
                        cities.append({
                            'name': city_name,
                            'region': region
                        })
        except Exception as e:
            print(f"Error loading Belgian cities: {e}")

        return cities

    def get_all_france_cities(self) -> List[str]:
        """Get all French city names"""
        return self.france_cities

    def get_all_wallonie_cities(self) -> List[str]:
        """Get all Wallonie city names only"""
        return [c['name'] for c in self.wallonie_cities]

    def get_all_cities(self, country: str = "France") -> List[str]:
        """Get all cities for specified country"""
        if country.lower() == "france":
            return self.france_cities
        elif country.lower() in ["belgium", "belgique", "wallonie"]:
            return self.get_all_wallonie_cities()
        else:
            # Return both for comprehensive search
            return self.france_cities + self.get_all_wallonie_cities()

    def get_city_count(self, country: str = None) -> Dict[str, int]:
        """Get city counts by region"""
        return {
            "france": len(self.france_cities),
            "wallonie": len(self.wallonie_cities),
            "total": len(self.france_cities) + len(self.wallonie_cities)
        }


# Global singleton instance
_cities_loader = None

def get_cities_loader() -> CitiesLoader:
    """Get or create cities loader singleton"""
    global _cities_loader
    if _cities_loader is None:
        _cities_loader = CitiesLoader()
    return _cities_loader
