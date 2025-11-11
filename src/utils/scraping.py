"""
Website scraping using Crawl4AI (free, local).

Best practice #2: Preprocess data to reduce token usage by 90%.
"""

import asyncio
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib


@dataclass
class ScrapedContent:
    """Scraped website content."""
    url: str
    markdown: str
    scraped_at: datetime
    token_count: int


# Simple in-memory cache (7 days TTL)
# In production, use Supabase cache table
_SCRAPING_CACHE: Dict[str, ScrapedContent] = {}
_CACHE_TTL_DAYS = 7


def _get_cache_key(url: str) -> str:
    """Generate cache key from URL."""
    return hashlib.md5(url.encode()).hexdigest()


async def scrape_website(
    url: str,
    use_cache: bool = True,
    max_length: int = 10000
) -> ScrapedContent:
    """
    Scrape website content using Crawl4AI.

    Best practice: Cache results to avoid re-scraping (95% savings).

    Args:
        url: Website URL to scrape
        use_cache: If True, check cache first
        max_length: Maximum content length (for preprocessing)

    Returns:
        ScrapedContent with markdown

    Example:
        >>> content = await scrape_website("https://aircall.io")
        >>> print(content.markdown[:100])
    """
    cache_key = _get_cache_key(url)

    # Check cache
    if use_cache and cache_key in _SCRAPING_CACHE:
        cached = _SCRAPING_CACHE[cache_key]
        age = datetime.now() - cached.scraped_at

        if age < timedelta(days=_CACHE_TTL_DAYS):
            return cached

    # Try importing Crawl4AI
    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError:
        # Fallback: Return empty content if Crawl4AI not installed
        return ScrapedContent(
            url=url,
            markdown="",
            scraped_at=datetime.now(),
            token_count=0
        )

    # Scrape
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        markdown = result.markdown or ""

        # Preprocessing: Limit length to reduce tokens
        if len(markdown) > max_length:
            markdown = markdown[:max_length] + "\n\n[Content truncated...]"

        content = ScrapedContent(
            url=url,
            markdown=markdown,
            scraped_at=datetime.now(),
            token_count=len(markdown) // 4  # Rough estimate
        )

        # Cache
        _SCRAPING_CACHE[cache_key] = content

        return content


async def scrape_specific_pages(
    base_url: str,
    pages: List[str],
    use_cache: bool = True
) -> Dict[str, ScrapedContent]:
    """
    Scrape specific pages from a website.

    Best practice: Only scrape relevant pages per agent (90% token reduction).

    Args:
        base_url: Base website URL (e.g., "https://aircall.io")
        pages: List of page paths (e.g., ["/", "/pricing", "/customers"])
        use_cache: If True, check cache first

    Returns:
        Dict mapping page path to ScrapedContent

    Example:
        >>> pages = await scrape_specific_pages(
        ...     "https://aircall.io",
        ...     ["/", "/pricing"]
        ... )
        >>> homepage = pages["/"]
        >>> pricing = pages["/pricing"]
    """
    base_url = base_url.rstrip("/")
    tasks = [
        scrape_website(f"{base_url}{page}", use_cache=use_cache)
        for page in pages
    ]

    results = await asyncio.gather(*tasks)

    return {
        page: content
        for page, content in zip(pages, results)
    }


# Smart page routing per agent type
AGENT_PAGE_ROUTING = {
    "persona_extractor": ["/", "/about"],
    "competitor_finder": ["/pricing", "/features"],
    "pain_point": ["/customers", "/case-studies", "/testimonials"],
    "signal_generator": ["/", "/blog"],
    "system_builder": ["/integrations", "/api"],
    "case_study": ["/customers", "/case-studies"]
}


async def scrape_for_agent(
    agent_type: str,
    website_url: str,
    use_cache: bool = True
) -> Dict[str, str]:
    """
    Scrape only relevant pages for a specific agent.

    Best practice: Smart scraping reduces tokens by 90%.

    Args:
        agent_type: Agent type (e.g., "persona_extractor")
        website_url: Website URL
        use_cache: If True, check cache first

    Returns:
        Dict mapping page path to markdown content

    Example:
        >>> content = await scrape_for_agent("persona_extractor", "https://aircall.io")
        >>> homepage = content["/"]
        >>> about = content["/about"]
    """
    if agent_type not in AGENT_PAGE_ROUTING:
        # Default: Just homepage
        pages = ["/"]
    else:
        pages = AGENT_PAGE_ROUTING[agent_type]

    results = await scrape_specific_pages(website_url, pages, use_cache)

    return {
        page: content.markdown
        for page, content in results.items()
    }


def preprocess_scraped_content(markdown: str, max_tokens: int = 2000) -> str:
    """
    Preprocess scraped content to reduce token usage.

    Best practice #2: Remove metadata, navigation, footers.

    Args:
        markdown: Raw markdown content
        max_tokens: Maximum tokens to keep

    Returns:
        Cleaned markdown
    """
    # Remove common metadata sections
    lines = markdown.split("\n")
    cleaned_lines = []

    skip_keywords = [
        "cookie", "privacy policy", "terms of service",
        "subscribe", "newsletter", "follow us",
        "copyright", "all rights reserved"
    ]

    for line in lines:
        line_lower = line.lower()

        # Skip metadata lines
        if any(keyword in line_lower for keyword in skip_keywords):
            continue

        # Skip navigation markers
        if line.startswith("##") and "navigation" in line_lower:
            continue

        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)

    # Limit length
    estimated_tokens = len(cleaned) // 4
    if estimated_tokens > max_tokens:
        char_limit = max_tokens * 4
        cleaned = cleaned[:char_limit] + "\n\n[Content truncated to reduce tokens...]"

    return cleaned


# Synchronous wrapper for non-async contexts
def scrape_website_sync(
    url: str,
    use_cache: bool = True,
    max_length: int = 10000
) -> ScrapedContent:
    """
    Synchronous wrapper for scrape_website.

    Args:
        url: Website URL
        use_cache: If True, check cache
        max_length: Max content length

    Returns:
        ScrapedContent
    """
    return asyncio.run(scrape_website(url, use_cache, max_length))


def scrape_for_agent_sync(
    agent_type: str,
    website_url: str,
    use_cache: bool = True
) -> Dict[str, str]:
    """
    Synchronous wrapper for scrape_for_agent.

    Args:
        agent_type: Agent type
        website_url: Website URL
        use_cache: If True, check cache

    Returns:
        Dict mapping page to content
    """
    return asyncio.run(scrape_for_agent(agent_type, website_url, use_cache))
