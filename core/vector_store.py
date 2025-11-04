"""
Vector Store Manager - Manages semantic paper search using Chroma
"""
from typing import List, Dict, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages vector storage for semantic paper search"""
    
    def __init__(self, 
                 collection_name: str = "research_papers",
                 embedding_model: str = "nomic-embed-text",
                 persist_directory: str = "./chroma_db"):
        """
        Initialize vector store
        
        Args:
            collection_name: Name of the Chroma collection
            embedding_model: Ollama embedding model
            persist_directory: Directory to persist vector data
        """
        try:
            from langchain_chroma import Chroma
            from langchain_ollama import OllamaEmbeddings
        except ImportError:
            logger.error("Chroma dependencies not installed. Run: pip install chromadb langchain-chroma")
            raise
        
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.persist_directory = Path(persist_directory)
        
        # Create directory if it doesn't exist
        self.persist_directory.mkdir(exist_ok=True, parents=True)
        
        # Initialize embeddings
        logger.info(f"Initializing embeddings with Ollama model: {embedding_model}")
        self.embeddings = OllamaEmbeddings(
            model=embedding_model,
            base_url="http://localhost:11434"
        )
        
        # Initialize Chroma vector store
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(self.persist_directory)
        )
        
        logger.info(f"VectorStore initialized: {collection_name} at {persist_directory}")
    
    def add_papers(self, papers: List[Dict]) -> List[str]:
        """
        Add papers to vector store
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            List of document IDs
        """
        from langchain_core.documents import Document
        
        if not papers:
            logger.warning("No papers to add to vector store")
            return []
        
        documents = []
        for paper in papers:
            # Create rich content combining title and abstract
            content = f"Title: {paper.get('title', 'Untitled')}\n\n"
            content += f"Abstract: {paper.get('abstract', 'No abstract available')}"
            
            # Prepare metadata
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
            
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)
        
        try:
            # Add documents to vector store
            ids = self.vectorstore.add_documents(documents)
            logger.info(f"Added {len(ids)} papers to vector store")
            return ids
        except Exception as e:
            logger.error(f"Error adding papers to vector store: {e}")
            return []
    
    def semantic_search(self, 
                       query: str, 
                       k: int = 10,
                       filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        Search for semantically similar papers
        
        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Metadata filters (e.g., {'source': 'arxiv'})
            
        Returns:
            List of similar papers with similarity scores
        """
        try:
            logger.info(f"Performing semantic search: '{query}' (k={k})")
            
            # Perform similarity search with scores
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
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def find_similar_papers(self, 
                          paper_id: str, 
                          k: int = 5) -> List[Dict]:
        """
        Find papers similar to a given paper
        
        Args:
            paper_id: ID of the reference paper
            k: Number of similar papers to return
            
        Returns:
            List of similar papers
        """
        try:
            # Get the reference paper
            results = self.vectorstore.get(
                where={'paper_id': paper_id}
            )
            
            if not results or not results.get('documents'):
                logger.warning(f"Paper not found in vector store: {paper_id}")
                return []
            
            # Search for similar content
            similar = self.vectorstore.similarity_search(
                results['documents'][0],
                k=k+1  # +1 because it includes the reference paper itself
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
        Check if paper semantically duplicates an existing paper
        
        Args:
            paper: Paper dictionary
            threshold: Similarity threshold (0-1, lower score = more similar)
            
        Returns:
            Duplicate paper info if found, None otherwise
        """
        try:
            content = f"Title: {paper.get('title', '')}\n\nAbstract: {paper.get('abstract', '')}"
            
            results = self.vectorstore.similarity_search_with_score(
                content,
                k=1
            )
            
            if results:
                doc, score = results[0]
                # Lower scores mean more similar in Chroma
                if score <= threshold:
                    logger.info(f"Semantic duplicate found: {paper.get('title', '')} (score: {score:.3f})")
                    return {
                        'duplicate_paper': doc.metadata,
                        'similarity_score': float(score),
                        'is_duplicate': True
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            return None
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the vector store collection"""
        try:
            collection = self.vectorstore._collection
            count = collection.count()
            
            return {
                'total_papers': count,
                'collection_name': self.collection_name,
                'embedding_model': self.embedding_model,
                'persist_directory': str(self.persist_directory)
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {
                'total_papers': 0,
                'collection_name': self.collection_name,
                'error': str(e)
            }
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            collection = self.vectorstore._collection
            # Get all IDs first
            all_ids = collection.get()['ids']
            if all_ids:
                collection.delete(ids=all_ids)
                logger.info(f"Cleared {len(all_ids)} documents from collection: {self.collection_name}")
            else:
                logger.info(f"Collection already empty: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
