"""IEEE Xplore API scraper for academic papers."""

import requests
import logging
from typing import List, Optional
from datetime import datetime
from .base_scraper import BaseScraper, ScrapedPaper

logger = logging.getLogger(__name__)


class IEEEScraper(BaseScraper):
    """
    Scraper for IEEE Xplore API.
    
    API Documentation: https://developer.ieee.org/
    Note: Requires API key from https://developer.ieee.org/member/register
    """
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize IEEE Xplore scraper.
        
        Args:
            api_key: IEEE API key (required for access)
            timeout: Request timeout in seconds
        """
        super().__init__(timeout=timeout, delay=1.0)
        self.api_key = api_key
        self.base_url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
        
        if not api_key:
            logger.warning("IEEE API key not provided. Set IEEE_API_KEY environment variable.")
    
    def search(self, query: str, max_results: int = 10) -> List[ScrapedPaper]:
        """
        Search IEEE Xplore for papers.
        
        Args:
            query: Search query string
            max_results: Maximum number of results (max 200 per request)
            
        Returns:
            List of ScrapedPaper objects
        """
        if not self.api_key:
            logger.error("IEEE API key required for search")
            return []
        
        papers = []
        
        try:
            self._rate_limit()
            
            # IEEE API parameters
            params = {
                'apikey': self.api_key,
                'querytext': query,
                'max_records': min(max_results, 200),  # Max 200 per request
                'start_record': 1,
                'sort_order': 'desc',
                'sort_field': 'article_number'
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout,
                headers={'Accept': 'application/json'}
            )
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            logger.info(f"IEEE Xplore API returned {len(articles)} results for query: {query}")
            
            for article in articles[:max_results]:
                paper = self._parse_ieee_article(article)
                if paper and self.validate_paper(paper):
                    papers.append(paper)
            
            logger.info(f"Successfully parsed {len(papers)} papers from IEEE Xplore")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"IEEE API request failed: {e}")
        except Exception as e:
            logger.error(f"Error parsing IEEE response: {e}", exc_info=True)
        
        return papers
    
    def _parse_ieee_article(self, article: dict) -> Optional[ScrapedPaper]:
        """Parse an IEEE API article into ScrapedPaper format."""
        try:
            # Extract basic metadata
            title = article.get('title', 'No Title')
            
            # Extract authors
            authors_data = article.get('authors', {}).get('authors', [])
            authors = [
                author.get('full_name', author.get('authorUrl', '').split('/')[-1])
                for author in authors_data
            ]
            
            # Extract abstract
            abstract = article.get('abstract', 'No abstract available')
            
            # Extract DOI and construct URL
            doi = article.get('doi', '')
            article_number = article.get('article_number', '')
            
            # IEEE document URL
            if doi:
                url = f"https://ieeexplore.ieee.org/document/{article_number}"
            else:
                url = article.get('html_url', '')
            
            # PDF URL
            pdf_url = article.get('pdf_url', None)
            
            # Extract publication date
            publication_year = article.get('publication_year')
            publication_date = None
            if publication_year:
                try:
                    publication_date = f"01 January {publication_year}"
                except:
                    publication_date = str(publication_year)
            
            # Extract venue/conference
            publication_title = article.get('publication_title', '')
            
            # Extract citation count (if available)
            citing_paper_count = article.get('citing_paper_count')
            citations = int(citing_paper_count) if citing_paper_count else None
            
            return ScrapedPaper(
                title=title,
                authors=authors,
                abstract=abstract,
                url=url,
                pdf_url=pdf_url,
                published_date=publication_date,
                doi=doi,
                venue=publication_title,
                citations=citations
            )
            
        except Exception as e:
            logger.error(f"Error parsing IEEE article: {e}", exc_info=True)
            return None
    
    def get_paper_details(self, article_number: str) -> Optional[ScrapedPaper]:
        """
        Get detailed information for a specific paper by article number.
        
        Args:
            article_number: IEEE article number
            
        Returns:
            ScrapedPaper object or None if not found
        """
        if not self.api_key:
            logger.error("IEEE API key required")
            return None
        
        try:
            self._rate_limit()
            
            params = {
                'apikey': self.api_key,
                'article_number': article_number,
                'max_records': 1
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout,
                headers={'Accept': 'application/json'}
            )
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            if articles:
                return self._parse_ieee_article(articles[0])
            
        except Exception as e:
            logger.error(f"Error fetching IEEE paper details: {e}", exc_info=True)
        
        return None
    
    def search_by_doi(self, doi: str) -> Optional[ScrapedPaper]:
        """
        Search for a paper by DOI.
        
        Args:
            doi: Paper DOI
            
        Returns:
            ScrapedPaper object or None if not found
        """
        if not self.api_key:
            logger.error("IEEE API key required")
            return None
        
        try:
            self._rate_limit()
            
            params = {
                'apikey': self.api_key,
                'querytext': f'"{doi}"',
                'max_records': 1
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout,
                headers={'Accept': 'application/json'}
            )
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            if articles:
                return self._parse_ieee_article(articles[0])
            
        except Exception as e:
            logger.error(f"Error searching IEEE by DOI: {e}", exc_info=True)
        
        return None
