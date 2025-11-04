"""Scraper manager to coordinate multiple scrapers with fallback logic."""

from typing import List, Optional, Dict
import logging
import os
from enum import Enum

from .base_scraper import BaseScraper, ScrapedPaper
from .arxiv_scraper import ArxivScraper
from .scholar_scraper import ScholarScraper
from .springer_scraper import SpringerScraper

logger = logging.getLogger(__name__)


class ScraperSource(Enum):
    """Available scraper sources."""
    ARXIV = "arxiv"
    SCHOLAR = "scholar"
    SPRINGER = "springer"


class ScraperManager:
    """
    Manages multiple scrapers with intelligent fallback logic.
    
    Tries API first, then falls back to web scraping if APIs are rate limited.
    Supports: arXiv, Semantic Scholar, Springer
    """
    
    def __init__(self, enable_scrapers: bool = True):
        """
        Initialize scraper manager.
        
        Args:
            enable_scrapers: Whether to enable web scraping fallback
        """
        self.enable_scrapers = enable_scrapers
        self.scrapers: Dict[ScraperSource, BaseScraper] = {}
        
        if enable_scrapers:
            # Initialize arXiv and Semantic Scholar (no API key required)
            self.scrapers[ScraperSource.ARXIV] = ArxivScraper()
            self.scrapers[ScraperSource.SCHOLAR] = ScholarScraper()
            
            # Initialize Springer (requires API key)
            springer_key = os.getenv('SPRINGER_API_KEY')
            if springer_key:
                self.scrapers[ScraperSource.SPRINGER] = SpringerScraper(api_key=springer_key)
                logger.info("Springer scraper initialized with API key")
            else:
                logger.warning("SPRINGER_API_KEY not set. Springer search disabled.")
            
            logger.info(f"Web scraping enabled with {len(self.scrapers)} sources")
        else:
            logger.info("Web scraping disabled")
    
    def search_with_fallback(
        self,
        query: str,
        source: ScraperSource,
        max_results: int = 10,
        api_failed: bool = False
    ) -> List[ScrapedPaper]:
        """
        Search with automatic fallback to web scraping.
        
        Args:
            query: Search query
            source: Which source to scrape
            max_results: Maximum results to return
            api_failed: Whether the API already failed (skip API retry)
            
        Returns:
            List of ScrapedPaper objects
        """
        if not self.enable_scrapers:
            logger.warning("Scraping disabled, no fallback available")
            return []
        
        if source not in self.scrapers:
            logger.error(f"Scraper for {source.value} not available")
            return []
        
        scraper = self.scrapers[source]
        
        try:
            if api_failed:
                logger.info(f"API failed, using {source.value} scraper as fallback")
            else:
                logger.info(f"Using {source.value} scraper")
            
            papers = scraper.search(query, max_results)
            
            if papers:
                logger.info(f"✓ Scraped {len(papers)} papers from {source.value}")
            else:
                logger.warning(f"No papers found via {source.value} scraper")
            
            return papers
            
        except Exception as e:
            logger.error(f"Scraper failed for {source.value}: {e}")
            return []
    
    def get_paper_details(
        self,
        paper_id: str,
        source: ScraperSource
    ) -> Optional[ScrapedPaper]:
        """
        Get detailed paper information.
        
        Args:
            paper_id: Paper identifier (arXiv ID, DOI, etc.)
            source: Which source to use
            
        Returns:
            ScrapedPaper object or None
        """
        if not self.enable_scrapers or source not in self.scrapers:
            return None
        
        scraper = self.scrapers[source]
        
        try:
            return scraper.get_paper_details(paper_id)
        except Exception as e:
            logger.error(f"Failed to get paper details from {source.value}: {e}")
            return None
    
    def convert_to_standard_format(self, scraped_paper: ScrapedPaper) -> Dict:
        """
        Convert ScrapedPaper to standard format used by research agent.
        
        Args:
            scraped_paper: ScrapedPaper object from scraper
            
        Returns:
            Dictionary in standard format
        """
        return {
            'title': scraped_paper.title,
            'authors': scraped_paper.authors,
            'abstract': scraped_paper.abstract,
            'url': scraped_paper.url,
            'pdf_url': scraped_paper.pdf_url,
            'published': scraped_paper.published_date,
            'arxiv_id': scraped_paper.arxiv_id,
            'doi': scraped_paper.doi,
            'venue': scraped_paper.venue,
            'citations': scraped_paper.citations or 0,
            'source': 'scraper'
        }
    
    def batch_convert(self, scraped_papers: List[ScrapedPaper]) -> List[Dict]:
        """
        Convert multiple scraped papers to standard format.
        
        Args:
            scraped_papers: List of ScrapedPaper objects
            
        Returns:
            List of dictionaries in standard format
        """
        return [self.convert_to_standard_format(p) for p in scraped_papers]
    
    def is_scholar_blocked(self) -> bool:
        """Check if Scholar scraper is blocked."""
        if ScraperSource.SCHOLAR in self.scrapers:
            scholar = self.scrapers[ScraperSource.SCHOLAR]
            if isinstance(scholar, ScholarScraper):
                return scholar.is_blocked()
        return False
    
    def reset_scholar_block(self):
        """Reset Scholar block status after waiting."""
        if ScraperSource.SCHOLAR in self.scrapers:
            scholar = self.scrapers[ScraperSource.SCHOLAR]
            if isinstance(scholar, ScholarScraper):
                scholar.reset_block_status()
