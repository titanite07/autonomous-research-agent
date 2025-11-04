"""
Data Collector Agent
Collects research papers from various sources
"""
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .base_agent import BaseAgent, AgentRole, Task
from scrapers.arxiv_scraper import ArxivScraper
from scrapers.semantic_scholar_scraper import SemanticScholarScraper


logger = logging.getLogger(__name__)


class DataCollectorAgent(BaseAgent):
    """
    Data Collector Agent: Collects research papers
    
    Responsibilities:
    - Search for papers on arXiv, Semantic Scholar, etc.
    - Download and extract paper metadata
    - Store papers for further processing
    - Handle rate limiting and errors
    """
    
    def __init__(
        self,
        agent_id: str = "data_collector",
        llm_config: Optional[Dict] = None,
        output_dir: Optional[Path] = None
    ):
        """
        Initialize Data Collector Agent
        
        Args:
            agent_id: Agent identifier
            llm_config: LLM configuration
            output_dir: Directory to store collected data
        """
        super().__init__(agent_id, AgentRole.DATA_COLLECTOR, llm_config)
        
        # Initialize scrapers
        self.arxiv_scraper = ArxivScraper()
        self.semantic_scholar_scraper = SemanticScholarScraper()
        
        # Output directory
        self.output_dir = output_dir or Path("data/collected_papers")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'papers_collected': 0,
            'queries_processed': 0,
            'errors': 0
        }
        
        self.logger.info(f"Data Collector Agent initialized (output: {self.output_dir})")
    
    async def process_task(self, task: Task) -> Any:
        """
        Process data collection tasks
        
        Args:
            task: Task to process
            
        Returns:
            Task result
        """
        if task.task_type == "collect_papers":
            return await self._collect_papers(task)
        elif task.task_type == "download_paper":
            return await self._download_paper(task)
        else:
            raise ValueError(f"Unknown task type: {task.task_type}")
    
    async def _collect_papers(self, task: Task) -> Dict:
        """
        Collect papers for a research query
        
        Args:
            task: Collection task
            
        Returns:
            Collection results
        """
        query = task.parameters.get('query', '')
        max_results = task.parameters.get('max_results', 20)
        sources = task.parameters.get('sources', ['arxiv', 'semantic_scholar'])
        
        self.logger.info(f"Collecting papers for query: {query}")
        
        collected_papers = []
        
        # Collect from arXiv
        if 'arxiv' in sources:
            try:
                arxiv_papers = await self._search_arxiv(query, max_results // 2)
                collected_papers.extend(arxiv_papers)
                self.logger.info(f"Collected {len(arxiv_papers)} papers from arXiv")
            except Exception as e:
                self.logger.error(f"Error collecting from arXiv: {e}")
                self.stats['errors'] += 1
        
        # Collect from Semantic Scholar
        if 'semantic_scholar' in sources:
            try:
                ss_papers = await self._search_semantic_scholar(query, max_results // 2)
                collected_papers.extend(ss_papers)
                self.logger.info(f"Collected {len(ss_papers)} papers from Semantic Scholar")
            except Exception as e:
                self.logger.error(f"Error collecting from Semantic Scholar: {e}")
                self.stats['errors'] += 1
        
        # Update statistics
        self.stats['papers_collected'] += len(collected_papers)
        self.stats['queries_processed'] += 1
        
        # Store in memory
        self.memory.store_long_term(f"query_{query}", collected_papers)
        
        result = {
            'query': query,
            'papers_collected': len(collected_papers),
            'papers': collected_papers,
            'sources': sources
        }
        
        self.logger.info(f"Collected {len(collected_papers)} total papers")
        
        return result
    
    async def _search_arxiv(self, query: str, max_results: int) -> List[Dict]:
        """
        Search arXiv for papers
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of paper metadata
        """
        try:
            papers = self.arxiv_scraper.search(query, max_results)
            
            return [
                {
                    'source': 'arxiv',
                    'paper_id': paper.get('arxiv_id', ''),
                    'title': paper.get('title', ''),
                    'authors': paper.get('authors', []),
                    'abstract': paper.get('abstract', ''),
                    'published_date': paper.get('published_date', ''),
                    'pdf_url': paper.get('pdf_url', ''),
                    'categories': paper.get('categories', [])
                }
                for paper in papers
            ]
        except Exception as e:
            self.logger.error(f"arXiv search failed: {e}")
            return []
    
    async def _search_semantic_scholar(self, query: str, max_results: int) -> List[Dict]:
        """
        Search Semantic Scholar for papers
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of paper metadata
        """
        try:
            papers = self.semantic_scholar_scraper.search(query, max_results)
            
            return [
                {
                    'source': 'semantic_scholar',
                    'paper_id': paper.get('paper_id', ''),
                    'title': paper.get('title', ''),
                    'authors': paper.get('authors', []),
                    'abstract': paper.get('abstract', ''),
                    'year': paper.get('year', ''),
                    'citation_count': paper.get('citation_count', 0),
                    'influential_citation_count': paper.get('influential_citation_count', 0),
                    'url': paper.get('url', '')
                }
                for paper in papers
            ]
        except Exception as e:
            self.logger.error(f"Semantic Scholar search failed: {e}")
            return []
    
    async def _download_paper(self, task: Task) -> Dict:
        """
        Download a specific paper
        
        Args:
            task: Download task
            
        Returns:
            Download result
        """
        paper_id = task.parameters.get('paper_id', '')
        source = task.parameters.get('source', 'arxiv')
        
        self.logger.info(f"Downloading paper {paper_id} from {source}")
        
        try:
            if source == 'arxiv':
                file_path = self.arxiv_scraper.download_pdf(
                    paper_id,
                    str(self.output_dir)
                )
            else:
                raise ValueError(f"Download not supported for source: {source}")
            
            return {
                'paper_id': paper_id,
                'source': source,
                'file_path': str(file_path),
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"Download failed for {paper_id}: {e}")
            self.stats['errors'] += 1
            
            return {
                'paper_id': paper_id,
                'source': source,
                'status': 'failed',
                'error': str(e)
            }
    
    def get_capabilities(self) -> List[str]:
        """Get data collector capabilities"""
        return [
            'data_collection',
            'paper_search',
            'pdf_download',
            'metadata_extraction'
        ]
    
    def get_statistics(self) -> Dict:
        """Get collection statistics"""
        return {
            **self.stats,
            'memory_size': len(self.memory.long_term)
        }
    
    def get_collected_papers(self, query: str) -> Optional[List[Dict]]:
        """
        Get papers collected for a query
        
        Args:
            query: Search query
            
        Returns:
            List of papers or None
        """
        return self.memory.retrieve_long_term(f"query_{query}")
