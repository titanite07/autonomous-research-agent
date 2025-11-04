"""
Milvus Vector Store Implementation
"""
from typing import List, Dict, Optional
import logging
import json

from .base import BaseVectorStore, VectorStoreConfig

logger = logging.getLogger(__name__)


class MilvusVectorStore(BaseVectorStore):
    """Milvus vector store implementation"""
    
    def __init__(self, config: VectorStoreConfig):
        """Initialize Milvus vector store"""
        super().__init__(config)
        
        try:
            from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
            from langchain_ollama import OllamaEmbeddings
        except ImportError as e:
            logger.error("Milvus dependencies not installed. Run: pip install pymilvus")
            raise ImportError("Missing dependencies: pymilvus") from e
        
        self.connections = connections
        self.Collection = Collection
        self.utility = utility
        
        # Connection settings
        self.host = config.host or "localhost"
        self.port = config.port or 19530
        
        # Initialize embeddings
        logger.info(f"Initializing Ollama embeddings: {config.embedding_model}")
        self.embeddings = OllamaEmbeddings(
            model=config.embedding_model,
            base_url=config.embedding_base_url
        )
        
        # Connect to Milvus
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise
        
        # Create collection if it doesn't exist
        self._create_collection(config)
        
        # Load collection
        self.collection = Collection(config.collection_name)
        self.collection.load()
        logger.info(f"Milvus collection loaded: {config.collection_name}")
    
    def _create_collection(self, config: VectorStoreConfig):
        """Create Milvus collection with schema"""
        from pymilvus import CollectionSchema, FieldSchema, DataType
        
        if self.utility.has_collection(config.collection_name):
            logger.info(f"Collection already exists: {config.collection_name}")
            return
        
        # Define schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="paper_id", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=config.embedding_dim),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="authors", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="year", dtype=DataType.VARCHAR, max_length=16),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="citations", dtype=DataType.INT64),
            FieldSchema(name="url", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="categories", dtype=DataType.VARCHAR, max_length=256)
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description=f"Research papers collection: {config.collection_name}"
        )
        
        # Create collection
        collection = self.Collection(
            name=config.collection_name,
            schema=schema
        )
        
        # Create index for vector field
        index_params = {
            "metric_type": config.distance_metric.upper(),  # COSINE, L2, IP
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        
        logger.info(f"Created Milvus collection: {config.collection_name}")
    
    def add_papers(self, papers: List[Dict]) -> List[str]:
        """Add papers to Milvus"""
        if not papers:
            logger.warning("No papers to add")
            return []
        
        try:
            # Prepare data for insertion
            paper_ids = []
            contents = []
            titles = []
            authors_list = []
            years = []
            sources = []
            citations_list = []
            urls = []
            categories_list = []
            
            for paper in papers:
                content = self._prepare_content(paper)
                metadata = self._prepare_metadata(paper)
                
                paper_ids.append(metadata['paper_id'])
                contents.append(content)
                titles.append(metadata['title'])
                authors_list.append(metadata['authors'])
                years.append(metadata['year'])
                sources.append(metadata['source'])
                citations_list.append(metadata['citations'])
                urls.append(metadata['url'])
                categories_list.append(metadata['categories'])
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(papers)} papers")
            embeddings = self.embeddings.embed_documents(contents)
            
            # Insert data
            entities = [
                paper_ids,
                embeddings,
                contents,
                titles,
                authors_list,
                years,
                sources,
                citations_list,
                urls,
                categories_list
            ]
            
            insert_result = self.collection.insert(entities)
            self.collection.flush()
            
            logger.info(f"Added {len(insert_result.primary_keys)} papers to Milvus")
            return [str(pk) for pk in insert_result.primary_keys]
            
        except Exception as e:
            logger.error(f"Error adding papers to Milvus: {e}")
            return []
    
    def semantic_search(self, 
                       query: str, 
                       k: int = 10,
                       filter_dict: Optional[Dict] = None) -> List[Dict]:
        """Search Milvus for similar papers"""
        try:
            logger.info(f"Milvus semantic search: '{query}' (k={k})")
            
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Prepare search parameters
            search_params = {
                "metric_type": self.config.distance_metric.upper(),
                "params": {"nprobe": 10}
            }
            
            # Build filter expression
            expr = None
            if filter_dict:
                conditions = [f'{k} == "{v}"' for k, v in filter_dict.items()]
                expr = " and ".join(conditions)
            
            # Search
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=k,
                expr=expr,
                output_fields=["paper_id", "title", "content", "authors", "year", 
                              "source", "citations", "url", "categories"]
            )
            
            # Parse results
            papers = []
            for hit in results[0]:
                paper = {
                    'similarity_score': float(hit.distance),
                    'paper_id': hit.entity.get('paper_id'),
                    'title': hit.entity.get('title'),
                    'content': hit.entity.get('content'),
                    'authors': hit.entity.get('authors'),
                    'year': hit.entity.get('year'),
                    'source': hit.entity.get('source'),
                    'citations': hit.entity.get('citations'),
                    'url': hit.entity.get('url'),
                    'categories': hit.entity.get('categories')
                }
                papers.append(paper)
            
            logger.info(f"Found {len(papers)} similar papers")
            return papers
            
        except Exception as e:
            logger.error(f"Milvus search error: {e}")
            return []
    
    def find_similar_papers(self, 
                          paper_id: str, 
                          k: int = 5) -> List[Dict]:
        """Find papers similar to a given paper"""
        try:
            # Query for the reference paper
            query_result = self.collection.query(
                expr=f'paper_id == "{paper_id}"',
                output_fields=["content"]
            )
            
            if not query_result:
                logger.warning(f"Paper not found: {paper_id}")
                return []
            
            # Use the content to search for similar papers
            content = query_result[0]['content']
            
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
        Check for semantic duplicates in Milvus
        
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
            
            # For COSINE: higher = more similar (threshold 0.90 = accept if > 0.90)
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
        """Delete papers from Milvus"""
        try:
            deleted_count = 0
            for paper_id in paper_ids:
                expr = f'paper_id == "{paper_id}"'
                self.collection.delete(expr)
                deleted_count += 1
            
            self.collection.flush()
            logger.info(f"Deleted {deleted_count} papers")
            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting papers: {e}")
            return 0
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict]:
        """Retrieve paper by ID from Milvus"""
        try:
            results = self.collection.query(
                expr=f'paper_id == "{paper_id}"',
                output_fields=["content", "title", "authors", "year", 
                              "source", "citations", "url", "categories"]
            )
            
            if not results:
                return None
            
            paper = results[0]
            return {
                'content': paper.get('content'),
                'metadata': {k: v for k, v in paper.items() if k != 'content'}
            }
        except Exception as e:
            logger.error(f"Error getting paper: {e}")
            return None
    
    def get_collection_stats(self) -> Dict:
        """Get Milvus collection statistics"""
        try:
            stats = self.collection.num_entities
            
            return {
                'total_papers': stats,
                'store_type': 'milvus',
                'collection_name': self.collection_name,
                'embedding_model': self.embedding_model,
                'host': self.host,
                'port': self.port,
                'distance_metric': self.config.distance_metric
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def clear_collection(self) -> bool:
        """Clear all data from Milvus collection"""
        try:
            # Delete all entities
            self.collection.delete(expr="id >= 0")
            self.collection.flush()
            logger.info(f"Cleared collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False
