"""Semantic Scholar API wrapper for academic paper search."""

from typing import List, Optional, Dict, Any
import requests
import logging
import time

from .base_scraper import BaseScraper, ScrapedPaper

logger = logging.getLogger(__name__)


class SemanticScholarScraper(BaseScraper):
    """
    Semantic Scholar API scraper for academic papers.
    Uses the official Semantic Scholar API (no authentication required for basic use).
    """
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    SEARCH_URL = f"{BASE_URL}/paper/search"
    
    def __init__(self, timeout: int = 30, delay: float = 1.0):
        """
        Initialize Semantic Scholar scraper.
        
        Args:
            timeout: Request timeout in seconds
            delay: Delay between requests (API is generous, 1s is sufficient)
        """
        super().__init__(timeout, delay)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Research-Agent/1.0 (mailto:researcher@example.com)',
            'Accept': 'application/json',
        })
    
    def search_papers(self, query: str, max_results: int = 10) -> List[ScrapedPaper]:
        """
        Search Semantic Scholar for papers (alias for search method).
        
        Args:
            query: Search query string
            max_results: Maximum number of papers to return
            
        Returns:
            List of scraped papers
        """
        return self.search(query, max_results)
    
    def search(self, query: str, max_results: int = 10) -> List[ScrapedPaper]:
        """
        Search Semantic Scholar API for papers.
        
        Args:
            query: Search query string
            max_results: Maximum number of papers to return (up to 100)
            
        Returns:
            List of ScrapedPaper objects
        """
        papers = []
        
        try:
            self._rate_limit()
            
            # Semantic Scholar API parameters
            params = {
                'query': query,
                'limit': min(max_results, 100),  # API max is 100
                'fields': 'paperId,title,abstract,authors,year,citationCount,url,venue,publicationTypes'
            }
            
            logger.info(f"Searching Semantic Scholar: '{query}'")
            response = self.session.get(
                self.SEARCH_URL, 
                params=params, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' not in data:
                logger.warning("No 'data' field in Semantic Scholar response")
                return papers
            
            results = data['data']
            logger.info(f"Found {len(results)} results from Semantic Scholar")
            
            # Parse results
            for result in results:
                try:
                    paper = self._parse_paper(result)
                    if paper and self.validate_paper(paper):
                        papers.append(paper)
                except Exception as e:
                    logger.error(f"Error parsing paper: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(papers)} papers from Semantic Scholar")
            
        except requests.RequestException as e:
            logger.error(f"Semantic Scholar API request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Semantic Scholar search: {e}")
        
        return papers
    
    def _parse_paper(self, data: Dict[str, Any]) -> Optional[ScrapedPaper]:
        """
        Parse a paper from Semantic Scholar API response.
        
        Args:
            data: Paper data from API
            
        Returns:
            ScrapedPaper object or None if parsing fails
        """
        try:
            # Extract paper ID
            paper_id = data.get('paperId', '')
            if not paper_id:
                return None
            
            # Extract title
            title = data.get('title', '').strip()
            if not title:
                return None
            
            # Extract authors
            authors = []
            for author in data.get('authors', []):
                if 'name' in author:
                    authors.append(author['name'])
            
            # Extract abstract
            abstract = data.get('abstract', '').strip() if data.get('abstract') else ''
            
            # Extract year
            year = data.get('year')
            year_str = str(year) if year else ''
            
            # Extract venue
            venue = data.get('venue', '').strip()
            
            # Extract URL
            url = data.get('url', '')
            if not url and paper_id:
                url = f"https://www.semanticscholar.org/paper/{paper_id}"
            
            # Extract citation count
            citation_count = data.get('citationCount', 0)
            
            # Extract publication types
            pub_types = data.get('publicationTypes', [])
            
            # Create ScrapedPaper object
            paper = ScrapedPaper(
                title=title,
                authors=authors,
                abstract=abstract,
                published_date=year_str,  # Changed from year= to published_date=
                url=url,
                doi=paper_id,  # Use paper_id as DOI for identification
                venue=venue,
                citations=citation_count,
                source='semantic_scholar'  # Mark as Semantic Scholar source
            )
            
            return paper
            
        except Exception as e:
            logger.error(f"Error parsing Semantic Scholar paper: {e}")
            return None
    
    def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper.
        
        Args:
            paper_id: Semantic Scholar paper ID
            
        Returns:
            Paper details or None if not found
        """
        try:
            self._rate_limit()
            
            url = f"{self.BASE_URL}/paper/{paper_id}"
            params = {
                'fields': 'paperId,title,abstract,authors,year,citationCount,url,venue,references,citations,publicationTypes,tldr'
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get paper details: {e}")
            return None
    
    def get_paper_citations(self, paper_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get papers that cite the given paper.
        
        Args:
            paper_id: Semantic Scholar paper ID
            limit: Maximum number of citations to retrieve
            
        Returns:
            List of citing papers
        """
        try:
            self._rate_limit()
            
            url = f"{self.BASE_URL}/paper/{paper_id}/citations"
            params = {
                'fields': 'paperId,title,authors,year,citationCount',
                'limit': min(limit, 1000)  # API max is 1000
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', [])
            
        except requests.RequestException as e:
            logger.error(f"Failed to get citations: {e}")
            return []
    
    def get_paper_references(self, paper_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get papers referenced by the given paper.
        
        Args:
            paper_id: Semantic Scholar paper ID
            limit: Maximum number of references to retrieve
            
        Returns:
            List of referenced papers
        """
        try:
            self._rate_limit()
            
            url = f"{self.BASE_URL}/paper/{paper_id}/references"
            params = {
                'fields': 'paperId,title,authors,year,citationCount',
                'limit': min(limit, 1000)  # API max is 1000
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', [])
            
        except requests.RequestException as e:
            logger.error(f"Failed to get references: {e}")
            return []
