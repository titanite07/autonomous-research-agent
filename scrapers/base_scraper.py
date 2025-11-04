"""Base scraper interface for all web scrapers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScrapedPaper:
    """Standardized paper data structure from scrapers."""
    title: str
    authors: List[str]
    abstract: str
    url: str
    pdf_url: Optional[str] = None
    published_date: Optional[str] = None
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    venue: Optional[str] = None
    citations: Optional[int] = None
    source: Optional[str] = None  # Source identifier: arxiv, springer, semantic_scholar, etc.
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'url': self.url,
            'pdf_url': self.pdf_url,
            'published_date': self.published_date,
            'arxiv_id': self.arxiv_id,
            'doi': self.doi,
            'venue': self.venue,
            'citations': self.citations,
            'source': self.source
        }


class BaseScraper(ABC):
    """Abstract base class for paper scrapers."""
    
    def __init__(self, timeout: int = 30, delay: float = 1.0):
        """
        Initialize scraper.
        
        Args:
            timeout: Request timeout in seconds
            delay: Delay between requests (rate limiting)
        """
        self.timeout = timeout
        self.delay = delay
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.delay:
            sleep_time = self.delay - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> List[ScrapedPaper]:
        """
        Search for papers matching query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of ScrapedPaper objects
        """
        pass
    
    @abstractmethod
    def get_paper_details(self, paper_id: str) -> Optional[ScrapedPaper]:
        """
        Get detailed information for a specific paper.
        
        Args:
            paper_id: Unique identifier for the paper
            
        Returns:
            ScrapedPaper object or None if not found
        """
        pass
    
    def validate_paper(self, paper: ScrapedPaper) -> bool:
        """
        Validate scraped paper has minimum required fields.
        
        Args:
            paper: ScrapedPaper to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not paper.title or len(paper.title.strip()) == 0:
            logger.warning("Paper missing title")
            return False
        
        if not paper.authors or len(paper.authors) == 0:
            logger.warning(f"Paper '{paper.title}' missing authors")
            return False
        
        if not paper.abstract or len(paper.abstract.strip()) < 50:
            logger.warning(f"Paper '{paper.title}' has insufficient abstract")
            return False
        
        return True
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Remove common artifacts
        text = text.replace("\n", " ")
        text = text.replace("\r", " ")
        text = text.replace("\t", " ")
        
        return text.strip()
