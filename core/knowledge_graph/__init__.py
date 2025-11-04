"""
Knowledge Graph Module
Comprehensive knowledge graph for research papers
"""

from .schema import (
    NodeType,
    EdgeType,
    NodeSchema,
    EdgeSchema,
    GraphStatistics,
    validate_node,
    validate_edge
)

from .entity_extractor import EntityExtractor

from .graph_builder import KnowledgeGraphBuilder

from .query_interface import KnowledgeGraphQuery

__all__ = [
    # Schema
    'NodeType',
    'EdgeType',
    'NodeSchema',
    'EdgeSchema',
    'GraphStatistics',
    'validate_node',
    'validate_edge',
    
    # Entity Extraction
    'EntityExtractor',
    
    # Graph Building
    'KnowledgeGraphBuilder',
    
    # Querying
    'KnowledgeGraphQuery',
]
