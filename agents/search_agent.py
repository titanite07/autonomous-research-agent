"""
Search Agent - Finds relevant academic papers from multiple sources
"""
import arxiv
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Paper:
    """Data class for academic paper"""
    title: str
    authors: List[str]
    abstract: str
    url: str
    pdf_url: Optional[str]
    published_date: datetime
    categories: List[str]
    paper_id: str
    citations: int = 0
    source: str = "arxiv"
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "url": self.url,
            "pdf_url": self.pdf_url,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "categories": self.categories,
            "paper_id": self.paper_id,
            "citations": self.citations,
            "source": self.source
        }


class SearchAgent:
    """Agent responsible for searching and retrieving academic papers"""
    
    def __init__(self, max_results: int = 20, sources: List[str] = None, use_vector_store: bool = False, dedup_threshold: float = 0.15):
        """
        Initialize SearchAgent
        
        Args:
            max_results: Maximum number of papers to return
            sources: List of sources to search (arxiv, semantic_scholar, google_scholar)
            use_vector_store: Enable vector store for semantic search
            dedup_threshold: Semantic similarity threshold for deduplication (0.05-0.30, default: 0.15)
        """
        self.max_results = max_results
        self.sources = sources or ["arxiv", "semantic_scholar"]
        self.arxiv_client = arxiv.Client()
        self.use_vector_store = use_vector_store
        self.vector_store = None
        self.dedup_threshold = dedup_threshold
        
        # Initialize vector store if enabled
        if use_vector_store:
            try:
                from core.vector_store import VectorStoreManager
                self.vector_store = VectorStoreManager()
                logger.info("Vector store enabled for semantic search")
            except ImportError:
                logger.warning("Vector store dependencies not available. Install with: pip install chromadb langchain-chroma")
                self.use_vector_store = False
        
        logger.info(f"SearchAgent initialized with sources: {self.sources}")
    
    def search_arxiv(self, query: str, max_results: int = None) -> List[Paper]:
        """
        Search arXiv for relevant papers
        
        Args:
            query: Search query string
            max_results: Maximum number of results (overrides default)
            
        Returns:
            List of Paper objects
        """
        max_results = max_results or self.max_results
        
        logger.info(f"Searching arXiv for: '{query}' (max_results={max_results})")
        
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            for result in self.arxiv_client.results(search):
                # Convert timezone-aware datetime to naive
                published_date = result.published
                if published_date and published_date.tzinfo is not None:
                    published_date = published_date.replace(tzinfo=None)
                
                paper = Paper(
                    title=result.title,
                    authors=[author.name for author in result.authors],
                    abstract=result.summary,
                    url=result.entry_id,
                    pdf_url=result.pdf_url,
                    published_date=published_date,
                    categories=result.categories,
                    paper_id=result.get_short_id(),
                    source="arxiv"
                )
                papers.append(paper)
            
            logger.info(f"Found {len(papers)} papers from arXiv")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching arXiv: {e}")
            return []
    
    def search_semantic_scholar(self, query: str, max_results: int = None) -> List[Paper]:
        """
        Search Semantic Scholar for relevant papers
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            
        Returns:
            List of Paper objects
        """
        max_results = max_results or self.max_results
        
        logger.info(f"Searching Semantic Scholar for: '{query}' (max_results={max_results})")
        
        try:
            from semanticscholar import SemanticScholar
            
            sch = SemanticScholar()
            results = sch.search_paper(query, limit=max_results)
            
            papers = []
            for result in results:
                # Parse publication date safely
                published_date = datetime.now()
                if result.publicationDate:
                    try:
                        # Handle different date formats
                        if isinstance(result.publicationDate, str):
                            published_date = datetime.fromisoformat(result.publicationDate)
                        elif isinstance(result.publicationDate, datetime):
                            published_date = result.publicationDate
                        
                        # Ensure timezone-naive for comparison
                        if published_date.tzinfo is not None:
                            published_date = published_date.replace(tzinfo=None)
                    except (ValueError, TypeError):
                        logger.debug(f"Could not parse date: {result.publicationDate}")
                        published_date = datetime.now()
                
                # Extract paper data
                paper = Paper(
                    title=result.title or "Untitled",
                    authors=[author.name for author in (result.authors or [])],
                    abstract=result.abstract or "",
                    url=f"https://www.semanticscholar.org/paper/{result.paperId}",
                    pdf_url=result.openAccessPdf.get('url') if result.openAccessPdf else None,
                    published_date=published_date,
                    categories=[result.venue or "General"],
                    paper_id=result.paperId,
                    citations=result.citationCount or 0,
                    source="semantic_scholar"
                )
                papers.append(paper)
            
            logger.info(f"Found {len(papers)} papers from Semantic Scholar")
            return papers
            
        except ImportError:
            logger.warning("semanticscholar package not installed. Install with: pip install semanticscholar")
            return []
        except Exception as e:
            logger.error(f"Error searching Semantic Scholar: {e}")
            return []
    
    def search(self, query: str, filters: Dict = None) -> List[Paper]:
        """
        Search all configured sources for relevant papers
        
        Args:
            query: Search query string
            filters: Optional filters (date_range, categories, etc.)
            
        Returns:
            Combined and deduplicated list of papers
        """
        logger.info(f"Starting comprehensive search for: '{query}'")
        
        all_papers = []
        
        # Search each source
        if "arxiv" in self.sources:
            arxiv_papers = self.search_arxiv(query)
            all_papers.extend(arxiv_papers)
        
        if "semantic_scholar" in self.sources:
            ss_papers = self.search_semantic_scholar(query)
            all_papers.extend(ss_papers)
        
        # Deduplicate by title similarity
        unique_papers = self._deduplicate_papers(all_papers)
        
        # Apply filters if provided
        if filters:
            unique_papers = self._apply_filters(unique_papers, filters)
        
        # Sort by citations (if available) and recency
        unique_papers.sort(key=lambda p: (p.citations, p.published_date), reverse=True)
        
        logger.info(f"Total unique papers found: {len(unique_papers)}")
        
        return unique_papers[:self.max_results]
    
    def _deduplicate_papers(self, papers: List[Paper]) -> List[Paper]:
        """
        Remove duplicate papers using semantic similarity (if vector store enabled) 
        or title matching (fallback)
        
        Args:
            papers: List of papers to deduplicate
            
        Returns:
            Deduplicated list of papers
        """
        if not papers:
            return []
        
        unique_papers = []
        duplicates_found = 0
        
        # Use semantic deduplication if vector store is available
        if self.use_vector_store and self.vector_store:
            logger.info("Using semantic deduplication (checking against vector store + within batch)")
            
            seen_paper_ids = set()
            seen_titles_normalized = set()  # For fast within-batch exact title matching
            
            for paper in papers:
                # Skip if exact duplicate by ID
                if paper.paper_id in seen_paper_ids:
                    duplicates_found += 1
                    continue
                
                # Quick check: exact title match within batch
                normalized_title = paper.title.lower().strip()
                if normalized_title in seen_titles_normalized:
                    logger.debug(f"Exact title duplicate in batch: {paper.title[:50]}...")
                    duplicates_found += 1
                    continue
                
                # Convert to dict for vector store
                paper_dict = paper.to_dict()
                
                # Semantic check: against existing papers in vector store
                duplicate_info = self.vector_store.check_semantic_duplicate(
                    paper_dict, 
                    threshold=self.dedup_threshold  # User-configurable threshold
                )
                
                if duplicate_info and duplicate_info.get('is_duplicate'):
                    # Found a semantic duplicate in existing collection
                    dup_paper = duplicate_info['duplicate_paper']
                    similarity_score = duplicate_info['similarity_score']
                    # Convert Chroma distance to similarity percentage
                    similarity_pct = (1 - similarity_score) * 100
                    logger.info(
                        f"Semantic duplicate found: '{paper.title[:45]}...' "
                        f"≈ '{dup_paper.get('title', '')[:45]}...' "
                        f"({similarity_pct:.1f}% similar, score: {similarity_score:.3f})"
                    )
                    duplicates_found += 1
                else:
                    # Not a duplicate - add to unique papers
                    unique_papers.append(paper)
                    seen_paper_ids.add(paper.paper_id)
                    seen_titles_normalized.add(normalized_title)
                    
                    # Important: Add this paper to vector store immediately
                    # so subsequent papers in this batch can be checked against it
                    try:
                        self.vector_store.add_papers([paper_dict])
                        logger.debug(f"Added to vector store for duplicate checking: {paper.title[:50]}...")
                    except Exception as e:
                        logger.warning(f"Failed to add paper to vector store: {e}")
        
        else:
            # Fallback to title-based deduplication
            logger.info("Using title-based deduplication (vector store disabled)")
            
            seen_titles = set()
            
            for paper in papers:
                # Normalize title for comparison
                normalized_title = paper.title.lower().strip()
                
                if normalized_title not in seen_titles:
                    seen_titles.add(normalized_title)
                    unique_papers.append(paper)
                else:
                    duplicates_found += 1
        
        logger.info(f"Deduplication complete: {len(unique_papers)} unique papers, {duplicates_found} duplicates removed")
        return unique_papers
    
    def _apply_filters(self, papers: List[Paper], filters: Dict) -> List[Paper]:
        """
        Apply filters to paper list
        
        Args:
            papers: List of papers to filter
            filters: Dictionary of filter criteria
            
        Returns:
            Filtered list of papers
        """
        filtered_papers = papers
        
        # Date range filter
        if "start_date" in filters:
            start_date = filters["start_date"]
            filtered_papers = [p for p in filtered_papers if p.published_date >= start_date]
        
        if "end_date" in filters:
            end_date = filters["end_date"]
            filtered_papers = [p for p in filtered_papers if p.published_date <= end_date]
        
        # Category filter
        if "categories" in filters:
            categories = filters["categories"]
            filtered_papers = [
                p for p in filtered_papers 
                if any(cat in p.categories for cat in categories)
            ]
        
        # Minimum citations filter
        if "min_citations" in filters:
            min_citations = filters["min_citations"]
            filtered_papers = [p for p in filtered_papers if p.citations >= min_citations]
        
        logger.info(f"Filtered down to {len(filtered_papers)} papers")
        return filtered_papers
    
    def expand_query(self, original_query: str) -> List[str]:
        """
        Generate variations of the search query for better coverage
        
        Args:
            original_query: Original search query
            
        Returns:
            List of query variations
        """
        # Basic query expansion (can be enhanced with LLM)
        queries = [original_query]
        
        # Add common variations
        words = original_query.split()
        if len(words) > 1:
            # Add quoted version for exact match
            queries.append(f'"{original_query}"')
            
            # Add variations with different orderings (simplified)
            if len(words) <= 4:
                queries.append(" ".join(reversed(words)))
        
        logger.info(f"Expanded query to {len(queries)} variations")
        return queries
    
    def semantic_search(self, query: str, k: int = None) -> List[Paper]:
        """
        Perform semantic search using vector store
        
        Args:
            query: Search query
            k: Number of results to return (overrides max_results)
            
        Returns:
            List of semantically similar papers
        """
        if not self.use_vector_store or self.vector_store is None:
            logger.warning("Vector store not enabled. Use --use-vector-store flag.")
            return []
        
        k = k or self.max_results
        
        try:
            results = self.vector_store.semantic_search(query, k=k)
            
            # Convert back to Paper objects
            papers = []
            for result in results:
                paper = Paper(
                    title=result.get('title', 'Untitled'),
                    authors=result.get('authors', '').split(', '),
                    abstract=result.get('content', '').split('\n\n')[-1].replace('Abstract: ', ''),
                    url=result.get('url', ''),
                    pdf_url=None,
                    published_date=datetime.now(),  # Placeholder
                    categories=result.get('categories', '').split(', '),
                    paper_id=result.get('paper_id', ''),
                    citations=int(result.get('citations', 0)),
                    source=result.get('source', 'vector_store')
                )
                papers.append(paper)
            
            logger.info(f"Semantic search found {len(papers)} papers")
            return papers
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def add_to_vector_store(self, papers: List[Paper]) -> bool:
        """
        Add papers to vector store for future semantic search
        
        Args:
            papers: List of Paper objects
            
        Returns:
            True if successful
        """
        if not self.use_vector_store or self.vector_store is None:
            return False
        
        try:
            paper_dicts = [p.to_dict() for p in papers]
            ids = self.vector_store.add_papers(paper_dicts)
            logger.info(f"Added {len(ids)} papers to vector store")
            return True
        except Exception as e:
            logger.error(f"Error adding papers to vector store: {e}")
            return False