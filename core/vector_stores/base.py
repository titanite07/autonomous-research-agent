"""
Base Vector Store Interface - Abstract class for all vector store implementations
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class VectorStoreConfig:
    """Configuration for vector store initialization"""
    store_type: str  # 'chroma', 'milvus', 'qdrant'
    collection_name: str = "research_papers"
    embedding_model: str = "nomic-embed-text"
    persist_directory: str = "./vector_db"
    
    # Optional provider-specific settings
    host: Optional[str] = None  # For Milvus/Qdrant
    port: Optional[int] = None  # For Milvus/Qdrant
    api_key: Optional[str] = None  # For cloud instances
    distance_metric: str = "cosine"  # 'cosine', 'l2', 'ip'
    
    # Embedding settings
    embedding_base_url: str = "http://localhost:11434"
    embedding_dim: int = 768  # Dimension for nomic-embed-text


class BaseVectorStore(ABC):
    """Abstract base class for vector store implementations"""
    
    def __init__(self, config: VectorStoreConfig):
        """
        Initialize vector store
        
        Args:
            config: Vector store configuration
        """
        self.config = config
        self.collection_name = config.collection_name
        self.embedding_model = config.embedding_model
        logger.info(f"Initializing {config.store_type} vector store: {config.collection_name}")
    
    @abstractmethod
    def add_papers(self, papers: List[Dict]) -> List[str]:
        """
        Add papers to vector store
        
        Args:
            papers: List of paper dictionaries with keys:
                - paper_id (str): Unique identifier
                - title (str): Paper title
                - abstract (str): Paper abstract
                - authors (List[str]): List of authors
                - published_date (str): Publication date
                - source (str): Data source (arxiv, semantic_scholar, etc.)
                - categories (List[str]): Paper categories/topics
                - citations (int): Citation count
                - url (str): Paper URL
                
        Returns:
            List of document IDs in the vector store
        """
        pass
    
    @abstractmethod
    def semantic_search(self, 
                       query: str, 
                       k: int = 10,
                       filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        Search for semantically similar papers
        
        Args:
            query: Search query string
            k: Number of results to return
            filter_dict: Metadata filters (e.g., {'source': 'arxiv', 'year': '2024'})
            
        Returns:
            List of papers with similarity scores:
                - similarity_score (float): Distance/similarity score
                - paper_id (str): Unique identifier
                - title (str): Paper title
                - content (str): Full text content
                - metadata (Dict): Additional metadata
        """
        pass
    
    @abstractmethod
    def find_similar_papers(self, 
                          paper_id: str, 
                          k: int = 5) -> List[Dict]:
        """
        Find papers similar to a given paper
        
        Args:
            paper_id: ID of the reference paper
            k: Number of similar papers to return
            
        Returns:
            List of similar papers (excluding the reference paper)
        """
        pass
    
    @abstractmethod
    def check_semantic_duplicate(self, 
                                paper: Dict, 
                                threshold: float = 0.90) -> Optional[Dict]:
        """
        Check if paper semantically duplicates an existing paper
        
        Args:
            paper: Paper dictionary to check
            threshold: Similarity threshold (interpretation varies by backend)
                      - Chroma (L2): lower score = more similar
                      - Milvus/Qdrant (cosine): higher score = more similar
            
        Returns:
            Duplicate paper info if found, None otherwise
        """
        pass
    
    @abstractmethod
    def delete_papers(self, paper_ids: List[str]) -> int:
        """
        Delete papers from vector store
        
        Args:
            paper_ids: List of paper IDs to delete
            
        Returns:
            Number of papers successfully deleted
        """
        pass
    
    @abstractmethod
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict]:
        """
        Retrieve a specific paper by ID
        
        Args:
            paper_id: Paper identifier
            
        Returns:
            Paper dictionary if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection
        
        Returns:
            Dictionary with stats:
                - total_papers (int): Total number of papers
                - store_type (str): Vector store backend
                - collection_name (str): Collection name
                - embedding_model (str): Embedding model name
        """
        pass
    
    @abstractmethod
    def clear_collection(self) -> bool:
        """
        Clear all data from the collection
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def _prepare_content(self, paper: Dict) -> str:
        """
        Prepare paper content for embedding
        
        Args:
            paper: Paper dictionary
            
        Returns:
            Formatted content string
        """
        content = f"Title: {paper.get('title', 'Untitled')}\n\n"
        content += f"Abstract: {paper.get('abstract', 'No abstract available')}"
        return content
    
    def _prepare_metadata(self, paper: Dict) -> Dict:
        """
        Prepare paper metadata for storage
        
        Args:
            paper: Paper dictionary
            
        Returns:
            Cleaned metadata dictionary
        """
        metadata = {
            'paper_id': paper.get('paper_id', ''),
            'title': paper.get('title', 'Untitled'),
            'authors': ', '.join(paper.get('authors', [])[:3]),  # First 3 authors
            'year': str(paper.get('published_date', ''))[:4] if paper.get('published_date') else 'Unknown',
            'source': paper.get('source', 'unknown'),
            'citations': paper.get('citations', 0),
            'url': paper.get('url', ''),
            'categories': ', '.join(paper.get('categories', [])[:2])  # First 2 categories
        }
        return metadata
    
    def health_check(self) -> bool:
        """
        Check if vector store is healthy and accessible
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            stats = self.get_collection_stats()
            return stats is not None
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
