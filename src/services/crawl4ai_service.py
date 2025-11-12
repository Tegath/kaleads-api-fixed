"""
Service de scraping avancé avec Crawl4AI

Remplace l'ancien système de scraping basique par Crawl4AI pour:
- Scraping plus intelligent et rapide
- Support de JavaScript/SPA
- Extraction de contenu de meilleure qualité
- Support de multiples pages en parallèle
"""

import asyncio
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import logging

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    logging.warning("Crawl4AI not installed. Falling back to basic scraping.")


logger = logging.getLogger(__name__)


class Crawl4AIService:
    """
    Service de scraping avancé utilisant Crawl4AI

    Features:
    - Scraping JavaScript/SPA
    - Extraction intelligente de contenu
    - Cache pour éviter re-scraping
    - Concurrent scraping
    - Fallback vers scraping basique si Crawl4AI indisponible
    """

    def __init__(self):
        self.available = CRAWL4AI_AVAILABLE
        if not self.available:
            logger.warning("Crawl4AI not available - using fallback scraping")

    async def scrape_url(
        self,
        url: str,
        format: str = "markdown",
        config: Optional[Dict] = None
    ) -> Dict:
        """
        Scrape une URL unique

        Args:
            url: URL à scraper
            format: Format de sortie (markdown, html, json, raw)
            config: Configuration Crawl4AI personnalisée

        Returns:
            Dict avec success, content, metadata
        """
        if not self.available:
            return await self._fallback_scrape(url)

        try:
            # Configuration du browser
            browser_config = BrowserConfig(
                headless=True,
                verbose=False,
                extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"]
            )

            # Configuration du crawler
            default_config = {
                "cache_mode": CacheMode.BYPASS,  # Toujours fetch fresh content
                "word_count_threshold": 10,
                "excluded_tags": ['nav', 'footer', 'header'],
                "remove_overlay_elements": True,
                "exclude_external_links": False,
            }

            if config:
                default_config.update(config)

            crawler_config = CrawlerRunConfig(**default_config)

            # Crawler
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(
                    url=url,
                    config=crawler_config
                )

                if not result.success:
                    logger.error(f"Crawl4AI failed for {url}: {result.error_message}")
                    return {
                        "success": False,
                        "url": url,
                        "error": result.error_message,
                        "content": None
                    }

                # Extraire le contenu selon le format demandé
                content = self._extract_content(result, format)

                # Extraire metadata
                metadata = {
                    "title": result.metadata.get("title", ""),
                    "description": result.metadata.get("description", ""),
                    "keywords": result.metadata.get("keywords", []),
                    "language": result.metadata.get("language", ""),
                    "author": result.metadata.get("author", ""),
                }

                return {
                    "success": True,
                    "url": url,
                    "content": content,
                    "metadata": metadata,
                    "status_code": result.status_code
                }

        except Exception as e:
            logger.error(f"Error scraping {url} with Crawl4AI: {str(e)}")
            return await self._fallback_scrape(url)

    async def scrape_multiple_pages(
        self,
        base_url: str,
        paths: List[str],
        format: str = "markdown",
        max_tokens: int = 5000
    ) -> Dict[str, str]:
        """
        Scrape plusieurs pages d'un même site en parallèle

        Args:
            base_url: URL de base du site
            paths: Liste des chemins relatifs à scraper
            format: Format de sortie
            max_tokens: Limite de tokens par page

        Returns:
            Dict {path: content}
        """
        # Construire les URLs complètes
        urls = {}
        for path in paths:
            full_url = urljoin(base_url, path)
            urls[path] = full_url

        # Scraper en parallèle
        tasks = [
            self.scrape_url(url, format=format)
            for url in urls.values()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combiner les résultats
        content_by_path = {}
        for path, result in zip(urls.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Error scraping {path}: {str(result)}")
                content_by_path[path] = ""
            elif result.get("success"):
                content = result.get("content", "")
                # Limiter les tokens
                content_by_path[path] = self._limit_tokens(content, max_tokens)
            else:
                content_by_path[path] = ""

        return content_by_path

    async def scrape_for_agent(
        self,
        agent_name: str,
        website: str,
        max_tokens: int = 5000
    ) -> Dict[str, str]:
        """
        Scrape spécifique pour un agent donné

        Chaque agent a des besoins différents:
        - PersonaExtractor: homepage + about
        - CompetitorFinder: homepage + features + pricing
        - PainPoint: homepage + customers + testimonials
        - SignalGenerator: homepage + blog + news + press
        - SystemBuilder: homepage + integrations + api + docs
        - CaseStudy: homepage + customers + case-studies + success-stories

        Args:
            agent_name: Nom de l'agent
            website: URL du site à scraper
            max_tokens: Limite de tokens totale

        Returns:
            Dict {page: content}
        """
        # Définir les pages pertinentes par agent
        pages_by_agent = {
            "persona_extractor": ["/", "/about", "/a-propos", "/qui-sommes-nous", "/company"],
            "competitor_finder": ["/", "/features", "/pricing", "/solutions", "/produits"],
            "pain_point": ["/", "/customers", "/temoignages", "/testimonials", "/case-studies"],
            "signal_generator": ["/", "/blog", "/actualites", "/news", "/press", "/presse"],
            "system_builder": ["/", "/integrations", "/api", "/docs", "/developers"],
            "case_study": ["/", "/customers", "/case-studies", "/success-stories", "/reussites", "/clients"],
        }

        paths = pages_by_agent.get(agent_name, ["/"])

        logger.info(f"Scraping for {agent_name}: {len(paths)} pages from {website}")

        return await self.scrape_multiple_pages(
            base_url=website,
            paths=paths,
            format="markdown",
            max_tokens=max_tokens // len(paths)  # Répartir équitablement
        )

    def _extract_content(self, result, format: str) -> str:
        """Extrait le contenu selon le format demandé"""
        if format == "markdown":
            return result.markdown or result.cleaned_html or result.html
        elif format == "html":
            return result.cleaned_html or result.html
        elif format == "json":
            return result.extracted_content or result.markdown
        else:  # raw
            return result.html

    def _limit_tokens(self, content: str, max_tokens: int) -> str:
        """
        Limite le contenu à max_tokens

        Approximation: 1 token ≈ 4 caractères
        """
        max_chars = max_tokens * 4
        if len(content) <= max_chars:
            return content
        return content[:max_chars] + "..."

    async def _fallback_scrape(self, url: str) -> Dict:
        """
        Scraping de fallback si Crawl4AI n'est pas disponible

        Utilise requests + BeautifulSoup basique
        """
        try:
            import requests
            from bs4 import BeautifulSoup

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extraire le texte
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()

            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            return {
                "success": True,
                "url": url,
                "content": text,
                "metadata": {
                    "title": soup.title.string if soup.title else "",
                },
                "status_code": response.status_code
            }

        except Exception as e:
            logger.error(f"Fallback scraping failed for {url}: {str(e)}")
            return {
                "success": False,
                "url": url,
                "error": str(e),
                "content": None
            }


# Instance globale
crawl4ai_service = Crawl4AIService()


# Helper functions pour compatibilité avec l'ancien système
async def scrape_for_agent_async(agent_name: str, website: str, max_tokens: int = 5000) -> Dict[str, str]:
    """
    Helper async pour scraper pour un agent

    Args:
        agent_name: Nom de l'agent (persona_extractor, competitor_finder, etc.)
        website: URL du site
        max_tokens: Limite de tokens

    Returns:
        Dict {page_path: content}
    """
    return await crawl4ai_service.scrape_for_agent(agent_name, website, max_tokens)


def scrape_for_agent_sync(agent_name: str, website: str, max_tokens: int = 5000) -> Dict[str, str]:
    """
    Helper synchrone pour scraper pour un agent

    Wrapper autour de la version async

    Args:
        agent_name: Nom de l'agent
        website: URL du site
        max_tokens: Limite de tokens

    Returns:
        Dict {page_path: content}
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Si déjà dans un event loop, créer une nouvelle task
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(crawl4ai_service.scrape_for_agent(agent_name, website, max_tokens))
        else:
            # Pas de loop actif, en créer un
            return asyncio.run(crawl4ai_service.scrape_for_agent(agent_name, website, max_tokens))
    except Exception as e:
        logger.error(f"Error in sync scraping: {str(e)}")
        return {}


def preprocess_scraped_content(combined_content: str, max_tokens: int = 5000) -> str:
    """
    Prétraite le contenu scrapé pour le limiter

    Args:
        combined_content: Contenu combiné
        max_tokens: Limite de tokens

    Returns:
        Contenu limité
    """
    max_chars = max_tokens * 4  # Approximation
    if len(combined_content) <= max_chars:
        return combined_content
    return combined_content[:max_chars] + "..."
