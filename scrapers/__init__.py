"""Web scraping module for bypassing API rate limits."""

from .base_scraper import BaseScraper, ScrapedPaper
from .arxiv_scraper import ArxivScraper
from .scholar_scraper import ScholarScraper
from .semantic_scholar_scraper import SemanticScholarScraper
from .springer_scraper import SpringerScraper
from .scraper_manager import ScraperManager, ScraperSource

__all__ = [
    'BaseScraper',
    'ScrapedPaper',
    'ArxivScraper',
    'ScholarScraper',
    'SemanticScholarScraper',
    'SpringerScraper',
    'ScraperManager',
    'ScraperSource'
]
