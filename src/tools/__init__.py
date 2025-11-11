"""
Outils utilitaires pour le système.
"""

from src.tools.web_scraper import WebScraper, scrape_company_website
from src.tools.validator import EmailValidator, validate_email, validate_email_detailed

__all__ = [
    "WebScraper",
    "scrape_company_website",
    "EmailValidator",
    "validate_email",
    "validate_email_detailed",
]
