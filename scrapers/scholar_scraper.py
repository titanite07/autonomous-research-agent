"""Google Scholar web scraper (use with caution - respect robots.txt)."""

from typing import List, Optional
import requests
from bs4 import BeautifulSoup
import re
import logging
import time
from urllib.parse import quote_plus

from .base_scraper import BaseScraper, ScrapedPaper

logger = logging.getLogger(__name__)


class ScholarScraper(BaseScraper):
    """
    Google Scholar scraper for academic paper search.
    
    WARNING: Google Scholar has strict rate limits and may block scrapers.
    Use this only as a last resort fallback and with significant delays.
    Consider using scholarly library or SerpAPI for production use.
    """
    
    BASE_URL = "https://scholar.google.com"
    SEARCH_URL = f"{BASE_URL}/scholar"
    
    def __init__(self, timeout: int = 30, delay: float = 10.0):
        """
        Initialize Scholar scraper.
        
        Args:
            timeout: Request timeout
            delay: Delay between requests (minimum 10s recommended)
        """
        super().__init__(timeout, max(delay, 10.0))
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self._blocked = False
    
    def search(self, query: str, max_results: int = 10) -> List[ScrapedPaper]:
        """
        Search Google Scholar.
        
        Args:
            query: Search query
            max_results: Maximum results (limited to 10 per page)
            
        Returns:
            List of ScrapedPaper objects
        """
        if self._blocked:
            logger.warning("Scholar scraper is blocked, skipping")
            return []
        
        papers = []
        
        try:
            self._rate_limit()
            
            params = {
                'q': query,
                'hl': 'en',
                'as_sdt': '0,5',
                'num': min(max_results, 10)
            }
            
            logger.info(f"Scraping Google Scholar: '{query}'")
            response = self.session.get(
                self.SEARCH_URL,
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 503 or 'CAPTCHA' in response.text:
                logger.error("Google Scholar blocked the request (CAPTCHA detected)")
                self._blocked = True
                return []
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all result entries
            results = soup.find_all('div', class_='gs_ri')
            
            for result in results[:max_results]:
                try:
                    paper = self._parse_result(result)
                    if paper and self.validate_paper(paper):
                        papers.append(paper)
                except Exception as e:
                    logger.error(f"Error parsing Scholar result: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(papers)} papers from Scholar")
            
        except requests.RequestException as e:
            logger.error(f"Scholar scraping failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Scholar scraping: {e}")
        
        return papers
    
    def _parse_result(self, result_element) -> Optional[ScrapedPaper]:
        """Parse a single Scholar search result."""
        try:
            # Extract title and URL
            title_elem = result_element.find('h3', class_='gs_rt')
            if not title_elem:
                return None
            
            title_link = title_elem.find('a')
            if title_link:
                title = self.clean_text(title_link.get_text())
                url = title_link['href']
            else:
                title = self.clean_text(title_elem.get_text())
                url = None
            
            # Extract authors and publication info
            authors_elem = result_element.find('div', class_='gs_a')
            authors = []
            venue = None
            published_date = None
            
            if authors_elem:
                authors_text = authors_elem.get_text()
                parts = authors_text.split(' - ')
                
                if len(parts) > 0:
                    author_list = parts[0].split(',')
                    authors = [self.clean_text(a) for a in author_list if a.strip()]
                
                if len(parts) > 1:
                    venue = self.clean_text(parts[1])
                
                if len(parts) > 2:
                    year_match = re.search(r'\d{4}', parts[2])
                    if year_match:
                        published_date = year_match.group(0)
            
            # Extract abstract/snippet
            abstract_elem = result_element.find('div', class_='gs_rs')
            abstract = ""
            if abstract_elem:
                abstract = self.clean_text(abstract_elem.get_text())
            
            # Extract citation count
            citations = None
            cite_elem = result_element.find('div', class_='gs_fl')
            if cite_elem:
                cite_link = cite_elem.find('a', string=re.compile(r'Cited by'))
                if cite_link:
                    cite_text = cite_link.get_text()
                    cite_match = re.search(r'Cited by (\d+)', cite_text)
                    if cite_match:
                        citations = int(cite_match.group(1))
            
            # Try to find PDF link
            pdf_url = None
            pdf_links = result_element.find_all('a', href=re.compile(r'\.pdf$'))
            if pdf_links:
                pdf_url = pdf_links[0]['href']
            
            # Try to extract DOI from URL
            doi = None
            if url:
                doi_match = re.search(r'doi\.org/(10\.\d+/[^\s&]+)', url)
                if doi_match:
                    doi = doi_match.group(1)
            
            return ScrapedPaper(
                title=title,
                authors=authors,
                abstract=abstract,
                url=url or "",
                pdf_url=pdf_url,
                published_date=published_date,
                venue=venue,
                citations=citations,
                doi=doi
            )
            
        except Exception as e:
            logger.error(f"Error parsing Scholar result element: {e}")
            return None
    
    def get_paper_details(self, paper_id: str) -> Optional[ScrapedPaper]:
        """
        Get paper details by cluster ID.
        
        Note: Google Scholar doesn't have stable paper IDs like arXiv.
        This method is limited in functionality.
        """
        logger.warning("Scholar get_paper_details not fully implemented")
        return None
    
    def is_blocked(self) -> bool:
        """Check if scraper has been blocked by Google Scholar."""
        return self._blocked
    
    def reset_block_status(self):
        """Reset block status (use after waiting significant time)."""
        self._blocked = False
        logger.info("Scholar scraper block status reset")
