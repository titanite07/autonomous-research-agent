"""ArXiv web scraper for bypassing API rate limits."""

from typing import List, Optional
import requests
from bs4 import BeautifulSoup
import re
import logging

from .base_scraper import BaseScraper, ScrapedPaper

logger = logging.getLogger(__name__)


class ArxivScraper(BaseScraper):
    """Scraper for arXiv using HTML parsing (fallback when API fails)."""
    
    BASE_URL = "https://arxiv.org"
    SEARCH_URL = f"{BASE_URL}/search/"
    
    def __init__(self, timeout: int = 30, delay: float = 3.0):
        """Initialize ArXiv scraper."""
        super().__init__(timeout, max(delay, 3.0))
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_papers(self, query: str, max_results: int = 10) -> List[ScrapedPaper]:
        """
        Search arXiv for papers (alias for search method).
        
        Args:
            query: Search query string
            max_results: Maximum number of papers to return
            
        Returns:
            List of scraped papers
        """
        return self.search(query, max_results)
    
    def search(self, query: str, max_results: int = 10) -> List[ScrapedPaper]:
        """Search arXiv using web scraping."""
        papers = []
        
        try:
            self._rate_limit()
            
            # arXiv only accepts 'query' and 'searchtype' parameters
            # Returns 50 results per page by default
            params = {
                'query': query,
                'searchtype': 'all'
            }
            
            logger.info(f"Scraping arXiv search: '{query}'")
            response = self.session.get(self.SEARCH_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = soup.find_all('li', class_='arxiv-result')
            
            if not results:
                logger.warning("No results found with class 'arxiv-result'")
                return papers
            
            logger.info(f"Found {len(results)} results on page")
            
            # Parse up to max_results papers
            for result in results[:max_results]:
                try:
                    paper = self._parse_result(result)
                    if paper and self.validate_paper(paper):
                        papers.append(paper)
                except Exception as e:
                    logger.error(f"Error parsing result: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(papers)} papers from arXiv")
            
        except requests.RequestException as e:
            logger.error(f"ArXiv scraping failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in arXiv scraping: {e}")
        
        return papers
    
    def _parse_result(self, result_element) -> Optional[ScrapedPaper]:
        """Parse a single search result element."""
        try:
            title_elem = result_element.find('p', class_='title')
            if not title_elem:
                return None
            title = self.clean_text(title_elem.get_text())
            
            arxiv_link = result_element.find('a', href=re.compile(r'/abs/'))
            if not arxiv_link:
                return None
            
            arxiv_id = arxiv_link['href'].split('/abs/')[-1]
            url = f"{self.BASE_URL}/abs/{arxiv_id}"
            pdf_url = f"{self.BASE_URL}/pdf/{arxiv_id}.pdf"
            
            authors_elem = result_element.find('p', class_='authors')
            authors = []
            if authors_elem:
                author_links = authors_elem.find_all('a')
                authors = [self.clean_text(a.get_text()) for a in author_links]
            
            abstract_elem = result_element.find('span', class_='abstract-full')
            if not abstract_elem:
                abstract_elem = result_element.find('span', class_='abstract-short')
            
            abstract = ""
            if abstract_elem:
                abstract = self.clean_text(abstract_elem.get_text())
                abstract = re.sub(r'^Abstract:\s*', '', abstract, flags=re.IGNORECASE)
            
            date_elem = result_element.find('p', class_='is-size-7')
            published_date = None
            if date_elem:
                date_text = date_elem.get_text()
                date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', date_text)
                if date_match:
                    published_date = date_match.group(1)
            
            subjects_elem = result_element.find('div', class_='tags')
            venue = None
            if subjects_elem:
                tags = subjects_elem.find_all('span', class_='tag')
                if tags:
                    venue = self.clean_text(tags[0].get_text())
            
            return ScrapedPaper(
                title=title,
                authors=authors,
                abstract=abstract,
                url=url,
                pdf_url=pdf_url,
                published_date=published_date,
                arxiv_id=arxiv_id,
                venue=venue,
                source='arxiv'  # Mark as arXiv source
            )
            
        except Exception as e:
            logger.error(f"Error parsing result element: {e}")
            return None
    
    def get_paper_details(self, paper_id: str) -> Optional[ScrapedPaper]:
        """Get detailed information for a specific paper by arXiv ID."""
        try:
            self._rate_limit()
            
            url = f"{self.BASE_URL}/abs/{paper_id}"
            logger.info(f"Fetching arXiv paper: {paper_id}")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title_elem = soup.find('h1', class_='title')
            if not title_elem:
                return None
            title = self.clean_text(title_elem.get_text().replace('Title:', ''))
            
            authors_elem = soup.find('div', class_='authors')
            authors = []
            if authors_elem:
                author_links = authors_elem.find_all('a')
                authors = [self.clean_text(a.get_text()) for a in author_links]
            
            abstract_elem = soup.find('blockquote', class_='abstract')
            abstract = ""
            if abstract_elem:
                abstract = self.clean_text(abstract_elem.get_text())
                abstract = re.sub(r'^Abstract:\s*', '', abstract, flags=re.IGNORECASE)
            
            dateline = soup.find('div', class_='dateline')
            published_date = None
            if dateline:
                date_match = re.search(r'\[Submitted.*?(\d{1,2}\s+\w+\s+\d{4})', dateline.get_text())
                if date_match:
                    published_date = date_match.group(1)
            
            subjects_elem = soup.find('td', class_='tablecell subjects')
            venue = None
            if subjects_elem:
                subjects = subjects_elem.get_text()
                venue = self.clean_text(subjects.split(';')[0]) if subjects else None
            
            doi_elem = soup.find('td', class_='tablecell arxivdoi')
            doi = None
            if doi_elem:
                doi_link = doi_elem.find('a')
                if doi_link:
                    doi = self.clean_text(doi_link.get_text())
            
            pdf_url = f"{self.BASE_URL}/pdf/{paper_id}.pdf"
            
            return ScrapedPaper(
                title=title,
                authors=authors,
                abstract=abstract,
                url=url,
                pdf_url=pdf_url,
                published_date=published_date,
                arxiv_id=paper_id,
                doi=doi,
                venue=venue,
                source='arxiv'  # Mark as arXiv source
            )
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch arXiv paper {paper_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing arXiv paper {paper_id}: {e}")
            return None
