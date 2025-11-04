"""Springer API scraper for academic papers."""

import requests
import logging
from typing import List, Optional
from datetime import datetime
from .base_scraper import BaseScraper, ScrapedPaper

logger = logging.getLogger(__name__)


class SpringerScraper(BaseScraper):
    """
    Scraper for Springer API.
    
    API Documentation: https://dev.springernature.com/
    Note: Requires API key from https://dev.springernature.com/signup
    """
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize Springer scraper.
        
        Args:
            api_key: Springer API key (required for access)
            timeout: Request timeout in seconds
        """
        super().__init__(timeout=timeout, delay=1.0)
        self.api_key = api_key
        self.base_url = "http://api.springernature.com/meta/v2/json"
        
        if not api_key:
            logger.warning("Springer API key not provided. Set SPRINGER_API_KEY environment variable.")
    
    def search(self, query: str, max_results: int = 10) -> List[ScrapedPaper]:
        """
        Search Springer for papers.
        
        Args:
            query: Search query string
            max_results: Maximum number of results (max 100 per request)
            
        Returns:
            List of ScrapedPaper objects
        """
        if not self.api_key:
            logger.error("Springer API key required for search")
            return []
        
        papers = []
        
        try:
            self._rate_limit()
            
            # Springer API parameters
            params = {
                'q': query,
                'api_key': self.api_key,
                's': 1,  # Start index
                'p': min(max_results, 100),  # Results per page (max 100)
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout,
                headers={'Accept': 'application/json'}
            )
            response.raise_for_status()
            
            data = response.json()
            records = data.get('records', [])
            
            logger.info(f"Springer API returned {len(records)} results for query: {query}")
            
            for record in records[:max_results]:
                paper = self._parse_springer_record(record)
                if paper and self.validate_paper(paper):
                    papers.append(paper)
            
            logger.info(f"Successfully parsed {len(papers)} papers from Springer")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Springer API request failed: {e}")
        except Exception as e:
            logger.error(f"Error parsing Springer response: {e}", exc_info=True)
        
        return papers
    
    def _parse_springer_record(self, record: dict) -> Optional[ScrapedPaper]:
        """Parse a Springer API record into ScrapedPaper format."""
        try:
            # Extract basic metadata
            title = record.get('title', 'No Title')
            
            # Extract authors
            creators = record.get('creators', [])
            authors = [creator.get('creator', '') for creator in creators if creator.get('creator')]
            
            # Extract abstract
            abstract = record.get('abstract', 'No abstract available')
            
            # Extract DOI and construct URL
            doi = record.get('doi', '')
            url = record.get('url', [{}])[0].get('value', f"https://doi.org/{doi}" if doi else '')
            
            # Extract publication date
            publication_date = record.get('publicationDate', '')
            if publication_date:
                try:
                    # Parse date (format: YYYY-MM-DD)
                    date_obj = datetime.strptime(publication_date, '%Y-%m-%d')
                    published_date = date_obj.strftime('%d %B %Y')
                except:
                    published_date = publication_date
            else:
                published_date = None
            
            # Extract venue/journal
            publication_name = record.get('publicationName', '')
            
            # PDF URL (if available)
            pdf_url = None
            for url_entry in record.get('url', []):
                if url_entry.get('format') == 'pdf':
                    pdf_url = url_entry.get('value')
                    break
            
            return ScrapedPaper(
                title=title,
                authors=authors,
                abstract=abstract,
                url=url,
                pdf_url=pdf_url,
                published_date=published_date,
                doi=doi,
                venue=publication_name,
                citations=None,  # Springer API doesn't provide citation count
                source='springer'  # Mark as Springer source
            )
            
        except Exception as e:
            logger.error(f"Error parsing Springer record: {e}", exc_info=True)
            return None
    
    def get_paper_details(self, doi: str) -> Optional[ScrapedPaper]:
        """
        Get detailed information for a specific paper by DOI.
        
        Args:
            doi: Paper DOI
            
        Returns:
            ScrapedPaper object or None if not found
        """
        if not self.api_key:
            logger.error("Springer API key required")
            return None
        
        try:
            self._rate_limit()
            
            params = {
                'q': f'doi:{doi}',
                'api_key': self.api_key,
                'p': 1
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout,
                headers={'Accept': 'application/json'}
            )
            response.raise_for_status()
            
            data = response.json()
            records = data.get('records', [])
            
            if records:
                return self._parse_springer_record(records[0])
            
        except Exception as e:
            logger.error(f"Error fetching Springer paper details: {e}", exc_info=True)
        
        return None
