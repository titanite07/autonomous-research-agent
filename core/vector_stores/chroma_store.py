"""
ChromaDB Vector Store Implementation
"""
from typing import List, Dict, Optional
from pathlib import Path
import logging

from .base import BaseVectorStore, VectorStoreConfig

logger = logging.getLogger(__name__)


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB vector store implementation"""
    
    def __init__(self, config: VectorStoreConfig):
        """Initialize ChromaDB vector store"""
        super().__init__(config)
        
        try:
            from langchain_chroma import Chroma
            from langchain_ollama import OllamaEmbeddings
        except ImportError as e:
            logger.error("ChromaDB dependencies not installed. Run: pip install chromadb langchain-chroma")
            raise ImportError("Missing dependencies: chromadb, langchain-chroma") from e
        
        # Create persist directory
        self.persist_directory = Path(config.persist_directory)
        self.persist_directory.mkdir(exist_ok=True, parents=True)
        
        # Initialize embeddings
        logger.info(f"Initializing Ollama embeddings: {config.embedding_model}")
        self.embeddings = OllamaEmbeddings(
            model=config.embedding_model,
            base_url=config.embedding_base_url
        )
        
        # Initialize Chroma vector store
        self.vectorstore = Chroma(
            collection_name=config.collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(self.persist_directory)
        )
        
        logger.info(f"ChromaDB initialized at {self.persist_directory}")
    
    def add_papers(self, papers: List[Dict]) -> List[str]:
        """Add papers to ChromaDB"""
        from langchain_core.documents import Document
        
        if not papers:
            logger.warning("No papers to add")
            return []
        
        documents = []
        for paper in papers:
            content = self._prepare_content(paper)
            metadata = self._prepare_metadata(paper)
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)
        
        try:
            ids = self.vectorstore.add_documents(documents)
            logger.info(f"Added {len(ids)} papers to ChromaDB")
            return ids
        except Exception as e:
            logger.error(f"Error adding papers: {e}")
            return []
    
    def semantic_search(self, 
                       query: str, 
                       k: int = 10,
                       filter_dict: Optional[Dict] = None) -> List[Dict]:
        """Search ChromaDB for similar papers"""
        try:
            logger.info(f"ChromaDB semantic search: '{query}' (k={k})")
            
            # Chroma uses L2 distance (lower = more similar)
            results = self.vectorstore.similarity_search_with_score(
                query, 
                k=k,
                filter=filter_dict
            )
            
            papers = []
            for doc, score in results:
                paper = {
                    'similarity_score': float(score),
                    'content': doc.page_content,
                    **doc.metadata
                }
                papers.append(paper)
            
            logger.info(f"Found {len(papers)} similar papers")
            return papers
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    def find_similar_papers(self, 
                          paper_id: str, 
                          k: int = 5) -> List[Dict]:
        """Find papers similar to a given paper"""
        try:
            # Get the reference paper
            results = self.vectorstore.get(
                where={'paper_id': paper_id}
            )
            
            if not results or not results.get('documents'):
                logger.warning(f"Paper not found: {paper_id}")
                return []
            
            # Search for similar content
            similar = self.vectorstore.similarity_search(
                results['documents'][0],
                k=k+1  # +1 because it includes the reference paper
            )
            
            # Filter out the original paper
            similar_papers = []
            for doc in similar:
                if doc.metadata.get('paper_id') != paper_id:
                    similar_papers.append({
                        'content': doc.page_content,
                        **doc.metadata
                    })
            
            logger.info(f"Found {len(similar_papers)} similar papers to {paper_id}")
            return similar_papers[:k]
            
        except Exception as e:
            logger.error(f"Error finding similar papers: {e}")
            return []
    
    def check_semantic_duplicate(self, 
                                paper: Dict, 
                                threshold: float = 0.90) -> Optional[Dict]:
        """
        Check for semantic duplicates in ChromaDB
        
        Note: Chroma uses L2 distance, so LOWER scores mean MORE similar
        """
        try:
            content = self._prepare_content(paper)
            
            # Search for very similar papers (k=1)
            results = self.vectorstore.similarity_search_with_score(content, k=1)
            
            if not results:
                return None
            
            doc, distance = results[0]
            
            # Chroma L2 distance: lower = more similar
            # Threshold 0.90 means accept if distance < 0.90
            if distance < threshold:
                logger.info(f"Potential duplicate found (distance: {distance:.3f})")
                return {
                    'paper_id': doc.metadata.get('paper_id'),
                    'title': doc.metadata.get('title'),
                    'distance': float(distance),
                    'is_duplicate': True
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking duplicate: {e}")
            return None
    
    def delete_papers(self, paper_ids: List[str]) -> int:
        """Delete papers from ChromaDB"""
        try:
            deleted_count = 0
            for paper_id in paper_ids:
                # Get document IDs matching this paper_id
                results = self.vectorstore.get(where={'paper_id': paper_id})
                if results and results.get('ids'):
                    self.vectorstore.delete(ids=results['ids'])
                    deleted_count += len(results['ids'])
            
            logger.info(f"Deleted {deleted_count} documents")
            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting papers: {e}")
            return 0
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict]:
        """Retrieve paper by ID from ChromaDB"""
        try:
            results = self.vectorstore.get(where={'paper_id': paper_id})
            
            if not results or not results.get('documents'):
                return None
            
            # Return first match
            return {
                'content': results['documents'][0],
                'metadata': results['metadatas'][0] if results.get('metadatas') else {}
            }
        except Exception as e:
            logger.error(f"Error getting paper: {e}")
            return None
    
    def get_collection_stats(self) -> Dict:
        """Get ChromaDB collection statistics"""
        try:
            collection = self.vectorstore._collection
            count = collection.count()
            
            return {
                'total_papers': count,
                'store_type': 'chromadb',
                'collection_name': self.collection_name,
                'embedding_model': self.embedding_model,
                'persist_directory': str(self.persist_directory),
                'distance_metric': 'l2'
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def clear_collection(self) -> bool:
        """Clear all data from ChromaDB collection"""
        try:
            collection = self.vectorstore._collection
            # Get all IDs and delete them
            all_data = collection.get()
            if all_data and all_data.get('ids'):
                collection.delete(ids=all_data['ids'])
                logger.info(f"Cleared collection: {self.collection_name}")
            else:
                logger.info(f"Collection already empty: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False


# Backward compatibility alias
ChromaStore = ChromaVectorStore
