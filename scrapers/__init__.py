"""Web scraping module for bypassing API rate limits."""

from .base_scraper import BaseScraper, ScrapedPaper
from .arxiv_scraper import ArxivScraper
from .scholar_scraper import ScholarScraper
from .scraper_manager import ScraperManager, ScraperSource

__all__ = [
    'BaseScraper',
    'ScrapedPaper',
    'ArxivScraper',
    'ScholarScraper',
    'ScraperManager',
    'ScraperSource'
]
