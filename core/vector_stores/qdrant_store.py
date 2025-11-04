"""
Qdrant Vector Store Implementation
"""
from typing import List, Dict, Optional
from pathlib import Path
import logging
import uuid

from .base import BaseVectorStore, VectorStoreConfig

logger = logging.getLogger(__name__)


class QdrantVectorStore(BaseVectorStore):
    """Qdrant vector store implementation"""
    
    def __init__(self, config: VectorStoreConfig):
        """Initialize Qdrant vector store"""
        super().__init__(config)
        
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams, PointStruct
            from langchain_ollama import OllamaEmbeddings
        except ImportError as e:
            logger.error("Qdrant dependencies not installed. Run: pip install qdrant-client")
            raise ImportError("Missing dependencies: qdrant-client") from e
        
        self.PointStruct = PointStruct
        
        # Initialize embeddings
        logger.info(f"Initializing Ollama embeddings: {config.embedding_model}")
        self.embeddings = OllamaEmbeddings(
            model=config.embedding_model,
            base_url=config.embedding_base_url
        )
        
        # Initialize Qdrant client
        if config.host and config.port:
            # Remote Qdrant instance
            self.client = QdrantClient(
                host=config.host,
                port=config.port,
                api_key=config.api_key
            )
            logger.info(f"Connected to remote Qdrant at {config.host}:{config.port}")
        else:
            # Local Qdrant (in-memory or file-based)
            persist_path = Path(config.persist_directory)
            persist_path.mkdir(exist_ok=True, parents=True)
            self.client = QdrantClient(path=str(persist_path))
            logger.info(f"Initialized local Qdrant at {persist_path}")
        
        # Map distance metrics
        distance_map = {
            'cosine': Distance.COSINE,
            'l2': Distance.EUCLID,
            'ip': Distance.DOT
        }
        self.distance = distance_map.get(config.distance_metric.lower(), Distance.COSINE)
        
        # Create collection if it doesn't exist
        self._create_collection(config)
    
    def _create_collection(self, config: VectorStoreConfig):
        """Create Qdrant collection with schema"""
        from qdrant_client.models import VectorParams
        
        collections = self.client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if config.collection_name in collection_names:
            logger.info(f"Collection already exists: {config.collection_name}")
            return
        
        # Create collection
        self.client.create_collection(
            collection_name=config.collection_name,
            vectors_config=VectorParams(
                size=config.embedding_dim,
                distance=self.distance
            )
        )
        
        # Create payload indexes for filtering
        self.client.create_payload_index(
            collection_name=config.collection_name,
            field_name="paper_id",
            field_schema="keyword"
        )
        self.client.create_payload_index(
            collection_name=config.collection_name,
            field_name="source",
            field_schema="keyword"
        )
        self.client.create_payload_index(
            collection_name=config.collection_name,
            field_name="year",
            field_schema="keyword"
        )
        
        logger.info(f"Created Qdrant collection: {config.collection_name}")
    
    def add_papers(self, papers: List[Dict]) -> List[str]:
        """Add papers to Qdrant"""
        if not papers:
            logger.warning("No papers to add")
            return []
        
        try:
            # Prepare data
            contents = []
            payloads = []
            
            for paper in papers:
                content = self._prepare_content(paper)
                metadata = self._prepare_metadata(paper)
                
                contents.append(content)
                payloads.append({
                    'paper_id': metadata['paper_id'],
                    'title': metadata['title'],
                    'content': content,
                    'authors': metadata['authors'],
                    'year': metadata['year'],
                    'source': metadata['source'],
                    'citations': metadata['citations'],
                    'url': metadata['url'],
                    'categories': metadata['categories']
                })
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(papers)} papers")
            embeddings = self.embeddings.embed_documents(contents)
            
            # Create points
            points = []
            point_ids = []
            for i, (embedding, payload) in enumerate(zip(embeddings, payloads)):
                point_id = str(uuid.uuid4())
                point_ids.append(point_id)
                points.append(
                    self.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                )
            
            # Upsert points
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Added {len(points)} papers to Qdrant")
            return point_ids
            
        except Exception as e:
            logger.error(f"Error adding papers to Qdrant: {e}")
            return []
    
    def semantic_search(self, 
                       query: str, 
                       k: int = 10,
                       filter_dict: Optional[Dict] = None) -> List[Dict]:
        """Search Qdrant for similar papers"""
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        try:
            logger.info(f"Qdrant semantic search: '{query}' (k={k})")
            
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Build filter
            query_filter = None
            if filter_dict:
                conditions = [
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filter_dict.items()
                ]
                query_filter = Filter(must=conditions)
            
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=k,
                query_filter=query_filter
            )
            
            # Parse results
            papers = []
            for hit in results:
                paper = {
                    'similarity_score': float(hit.score),
                    'paper_id': hit.payload.get('paper_id'),
                    'title': hit.payload.get('title'),
                    'content': hit.payload.get('content'),
                    'authors': hit.payload.get('authors'),
                    'year': hit.payload.get('year'),
                    'source': hit.payload.get('source'),
                    'citations': hit.payload.get('citations'),
                    'url': hit.payload.get('url'),
                    'categories': hit.payload.get('categories')
                }
                papers.append(paper)
            
            logger.info(f"Found {len(papers)} similar papers")
            return papers
            
        except Exception as e:
            logger.error(f"Qdrant search error: {e}")
            return []
    
    def find_similar_papers(self, 
                          paper_id: str, 
                          k: int = 5) -> List[Dict]:
        """Find papers similar to a given paper"""
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        try:
            # Query for the reference paper
            filter_condition = Filter(
                must=[FieldCondition(key="paper_id", match=MatchValue(value=paper_id))]
            )
            
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_condition,
                limit=1,
                with_payload=True
            )
            
            if not results[0]:
                logger.warning(f"Paper not found: {paper_id}")
                return []
            
            # Use the content to search for similar papers
            content = results[0][0].payload.get('content', '')
            
            # Search for similar papers
            similar_papers = self.semantic_search(content, k=k+1)
            
            # Filter out the original paper
            filtered = [p for p in similar_papers if p['paper_id'] != paper_id]
            
            logger.info(f"Found {len(filtered)} similar papers to {paper_id}")
            return filtered[:k]
            
        except Exception as e:
            logger.error(f"Error finding similar papers: {e}")
            return []
    
    def check_semantic_duplicate(self, 
                                paper: Dict, 
                                threshold: float = 0.90) -> Optional[Dict]:
        """
        Check for semantic duplicates in Qdrant
        
        Note: With COSINE metric, HIGHER scores mean MORE similar (max = 1.0)
        """
        try:
            content = self._prepare_content(paper)
            
            # Search for very similar papers
            results = self.semantic_search(content, k=1)
            
            if not results:
                return None
            
            top_match = results[0]
            similarity = top_match['similarity_score']
            
            # For COSINE: higher = more similar
            if similarity > threshold:
                logger.info(f"Potential duplicate found (similarity: {similarity:.3f})")
                return {
                    'paper_id': top_match['paper_id'],
                    'title': top_match['title'],
                    'similarity': float(similarity),
                    'is_duplicate': True
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking duplicate: {e}")
            return None
    
    def delete_papers(self, paper_ids: List[str]) -> int:
        """Delete papers from Qdrant"""
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        try:
            deleted_count = 0
            for paper_id in paper_ids:
                filter_condition = Filter(
                    must=[FieldCondition(key="paper_id", match=MatchValue(value=paper_id))]
                )
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=filter_condition
                )
                deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} papers")
            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting papers: {e}")
            return 0
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict]:
        """Retrieve paper by ID from Qdrant"""
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        try:
            filter_condition = Filter(
                must=[FieldCondition(key="paper_id", match=MatchValue(value=paper_id))]
            )
            
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_condition,
                limit=1,
                with_payload=True
            )
            
            if not results[0]:
                return None
            
            payload = results[0][0].payload
            return {
                'content': payload.get('content'),
                'metadata': {k: v for k, v in payload.items() if k != 'content'}
            }
        except Exception as e:
            logger.error(f"Error getting paper: {e}")
            return None
    
    def get_collection_stats(self) -> Dict:
        """Get Qdrant collection statistics"""
        try:
            info = self.client.get_collection(self.collection_name)
            
            return {
                'total_papers': info.points_count,
                'store_type': 'qdrant',
                'collection_name': self.collection_name,
                'embedding_model': self.embedding_model,
                'distance_metric': self.config.distance_metric,
                'vector_size': info.config.params.vectors.size
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def clear_collection(self) -> bool:
        """Clear all data from Qdrant collection"""
        try:
            # Delete and recreate collection
            self.client.delete_collection(self.collection_name)
            self._create_collection(self.config)
            logger.info(f"Cleared collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False
