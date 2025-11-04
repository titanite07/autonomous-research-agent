"""
Vector Store Factory - Intelligently creates vector store instances
"""
from typing import Optional
import logging

from .base import BaseVectorStore, VectorStoreConfig
from .chroma_store import ChromaVectorStore
from .milvus_store import MilvusVectorStore
from .qdrant_store import QdrantVectorStore

logger = logging.getLogger(__name__)


class VectorStoreFactory:
    """Factory for creating vector store instances"""
    
    # Registry of available stores
    STORES = {
        'chroma': ChromaVectorStore,
        'chromadb': ChromaVectorStore,
        'milvus': MilvusVectorStore,
        'qdrant': QdrantVectorStore
    }
    
    @classmethod
    def create(cls, config: VectorStoreConfig) -> BaseVectorStore:
        """
        Create a vector store instance based on configuration
        
        Args:
            config: Vector store configuration
            
        Returns:
            Initialized vector store instance
            
        Raises:
            ValueError: If store type is not supported
            ImportError: If required dependencies are not installed
        """
        store_type = config.store_type.lower()
        
        if store_type not in cls.STORES:
            available = ', '.join(cls.STORES.keys())
            raise ValueError(
                f"Unsupported vector store: '{store_type}'. "
                f"Available options: {available}"
            )
        
        store_class = cls.STORES[store_type]
        
        try:
            logger.info(f"Creating {store_type} vector store...")
            instance = store_class(config)
            
            # Health check
            if instance.health_check():
                logger.info(f"✓ {store_type} vector store ready")
                return instance
            else:
                logger.warning(f"⚠ {store_type} vector store created but health check failed")
                return instance
                
        except ImportError as e:
            logger.error(f"Missing dependencies for {store_type}: {e}")
            cls._show_installation_instructions(store_type)
            raise
        except Exception as e:
            logger.error(f"Failed to create {store_type} vector store: {e}")
            raise
    
    @classmethod
    def create_from_dict(cls, config_dict: dict) -> BaseVectorStore:
        """
        Create vector store from dictionary configuration
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            Initialized vector store instance
        """
        config = VectorStoreConfig(**config_dict)
        return cls.create(config)
    
    @classmethod
    def _show_installation_instructions(cls, store_type: str):
        """Show installation instructions for missing dependencies"""
        instructions = {
            'chroma': "pip install chromadb langchain-chroma",
            'chromadb': "pip install chromadb langchain-chroma",
            'milvus': "pip install pymilvus",
            'qdrant': "pip install qdrant-client"
        }
        
        install_cmd = instructions.get(store_type, "Unknown")
        logger.info(f"\nTo use {store_type}, install dependencies:")
        logger.info(f"  {install_cmd}\n")
    
    @classmethod
    def list_available_stores(cls) -> list:
        """
        List all available vector store types
        
        Returns:
            List of store type strings
        """
        return list(set(cls.STORES.keys()))
    
    @classmethod
    def check_dependencies(cls, store_type: str) -> bool:
        """
        Check if dependencies for a store type are installed
        
        Args:
            store_type: Vector store type to check
            
        Returns:
            True if dependencies are available, False otherwise
        """
        store_type = store_type.lower()
        
        if store_type not in cls.STORES:
            return False
        
        try:
            if store_type in ['chroma', 'chromadb']:
                import chromadb
                import langchain_chroma
            elif store_type == 'milvus':
                import pymilvus
            elif store_type == 'qdrant':
                import qdrant_client
            return True
        except ImportError:
            return False
    
    @classmethod
    def get_recommended_store(cls) -> Optional[str]:
        """
        Get recommended vector store based on available dependencies
        
        Returns:
            Store type string or None if no stores available
        """
        # Priority order: Qdrant > Milvus > ChromaDB
        preferences = ['qdrant', 'milvus', 'chroma']
        
        for store_type in preferences:
            if cls.check_dependencies(store_type):
                logger.info(f"Recommended vector store: {store_type}")
                return store_type
        
        logger.warning("No vector store dependencies found")
        return None
    
    @classmethod
    def auto_select(cls, 
                   collection_name: str = "research_papers",
                   embedding_model: str = "nomic-embed-text",
                   persist_directory: str = "./vector_db") -> Optional[BaseVectorStore]:
        """
        Automatically select and create the best available vector store
        
        Args:
            collection_name: Name for the collection
            embedding_model: Embedding model to use
            persist_directory: Directory for persistent storage
            
        Returns:
            Vector store instance or None if no stores available
        """
        store_type = cls.get_recommended_store()
        
        if not store_type:
            logger.error("Cannot auto-select: No vector store dependencies installed")
            logger.info("\nInstall at least one of:")
            logger.info("  - ChromaDB: pip install chromadb langchain-chroma")
            logger.info("  - Milvus: pip install pymilvus")
            logger.info("  - Qdrant: pip install qdrant-client")
            return None
        
        config = VectorStoreConfig(
            store_type=store_type,
            collection_name=collection_name,
            embedding_model=embedding_model,
            persist_directory=persist_directory
        )
        
        return cls.create(config)
