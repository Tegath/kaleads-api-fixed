"""
Web Scraper Tool

Scrape website content pour enrichir les données des contacts.
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import time
from urllib.parse import urljoin, urlparse


class WebScraper:
    """
    Outil pour scraper le contenu de sites web.

    Features:
    - Scrape homepage, about page, customers page
    - Extract meta description, title
    - Extract testimonials and case studies
    - Gère les erreurs (404, timeout, etc.)
    """

    def __init__(self, timeout: int = 10, user_agent: Optional[str] = None):
        """
        Initialise le scraper.

        Args:
            timeout: Timeout en secondes pour les requêtes HTTP
            user_agent: User agent personnalisé (optionnel)
        """
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def scrape_website(self, url: str) -> Dict[str, str]:
        """
        Scrape un site web et retourne le contenu structuré.

        Args:
            url: URL du site web à scraper

        Returns:
            Dict avec:
            - homepage_content: Contenu de la page d'accueil
            - meta_description: Meta description
            - title: Titre de la page
            - about_content: Contenu de la page "about" (si trouvée)
            - customers_content: Contenu de la page "customers" (si trouvée)
            - testimonials: Liste des témoignages trouvés
            - error: Message d'erreur (si erreur)
        """
        result = {
            "homepage_content": "",
            "meta_description": "",
            "title": "",
            "about_content": "",
            "customers_content": "",
            "testimonials": [],
            "error": None
        }

        try:
            # 1. Scrape homepage
            homepage_data = self._scrape_page(url)
            if homepage_data["error"]:
                result["error"] = homepage_data["error"]
                return result

            result["homepage_content"] = homepage_data["content"]
            result["meta_description"] = homepage_data["meta_description"]
            result["title"] = homepage_data["title"]

            # 2. Try to find and scrape "about" page
            about_url = self._find_page_url(url, ["about", "about-us", "who-we-are", "company"])
            if about_url:
                about_data = self._scrape_page(about_url)
                if not about_data["error"]:
                    result["about_content"] = about_data["content"]

            # 3. Try to find and scrape "customers" or "case studies" page
            customers_url = self._find_page_url(url, ["customers", "clients", "case-studies", "success-stories"])
            if customers_url:
                customers_data = self._scrape_page(customers_url)
                if not customers_data["error"]:
                    result["customers_content"] = customers_data["content"]

            # 4. Extract testimonials from homepage
            result["testimonials"] = self._extract_testimonials(homepage_data["soup"])

        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"

        return result

    def _scrape_page(self, url: str) -> Dict:
        """
        Scrape une page individuelle.

        Args:
            url: URL de la page

        Returns:
            Dict avec content, meta_description, title, soup, error
        """
        result = {
            "content": "",
            "meta_description": "",
            "title": "",
            "soup": None,
            "error": None
        }

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            result["soup"] = soup

            # Extract title
            title_tag = soup.find("title")
            if title_tag:
                result["title"] = title_tag.get_text(strip=True)

            # Extract meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                result["meta_description"] = meta_desc["content"]

            # Extract main content (remove scripts, styles, etc.)
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text content
            text = soup.get_text(separator=" ", strip=True)
            # Clean up whitespace
            text = " ".join(text.split())
            result["content"] = text[:5000]  # Limit to 5000 chars

        except requests.exceptions.Timeout:
            result["error"] = f"Timeout ({self.timeout}s) while fetching {url}"
        except requests.exceptions.HTTPError as e:
            result["error"] = f"HTTP error {e.response.status_code} for {url}"
        except requests.exceptions.RequestException as e:
            result["error"] = f"Request error for {url}: {str(e)}"
        except Exception as e:
            result["error"] = f"Error parsing {url}: {str(e)}"

        return result

    def _find_page_url(self, base_url: str, keywords: list) -> Optional[str]:
        """
        Essaye de trouver l'URL d'une page spécifique (about, customers, etc.).

        Args:
            base_url: URL de base du site
            keywords: Liste de mots-clés à chercher (ex: ["about", "about-us"])

        Returns:
            URL trouvée ou None
        """
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        # Essayer chaque keyword
        for keyword in keywords:
            # Essayer avec et sans tiret
            for variant in [keyword, keyword.replace("-", "")]:
                test_url = f"{base}/{variant}"
                try:
                    response = self.session.head(test_url, timeout=5, allow_redirects=True)
                    if response.status_code == 200:
                        return test_url
                except:
                    continue

        return None

    def _extract_testimonials(self, soup) -> list:
        """
        Extrait les témoignages depuis le HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            Liste de témoignages (texte)
        """
        if not soup:
            return []

        testimonials = []

        # Chercher des éléments avec classes communes pour les testimonials
        testimonial_keywords = ["testimonial", "review", "quote", "feedback", "customer-story"]

        for keyword in testimonial_keywords:
            elements = soup.find_all(class_=lambda x: x and keyword in x.lower())
            for elem in elements[:3]:  # Max 3 témoignages
                text = elem.get_text(strip=True)
                if 50 < len(text) < 500:  # Filtrer par longueur raisonnable
                    testimonials.append(text)

        return testimonials


# Fonction helper pour utilisation simple
def scrape_company_website(url: str) -> Dict[str, str]:
    """
    Helper function pour scraper un site web rapidement.

    Args:
        url: URL du site à scraper

    Returns:
        Dict avec le contenu scrapé
    """
    scraper = WebScraper()
    return scraper.scrape_website(url)
