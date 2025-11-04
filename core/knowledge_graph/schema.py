"""
Knowledge Graph Schema Definition
Defines node types, edge types, and properties for the research paper knowledge graph
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime


class NodeType(Enum):
    """Types of nodes in the knowledge graph"""
    PAPER = "paper"
    AUTHOR = "author"
    CONCEPT = "concept"
    METHOD = "method"
    DATASET = "dataset"
    INSTITUTION = "institution"
    VENUE = "venue"  # Conference or journal


class EdgeType(Enum):
    """Types of edges (relationships) in the knowledge graph"""
    CITES = "cites"  # Paper -> Paper
    CITED_BY = "cited_by"  # Paper -> Paper (inverse of CITES)
    AUTHORED_BY = "authored_by"  # Paper -> Author
    AFFILIATED_WITH = "affiliated_with"  # Author -> Institution
    USES_METHOD = "uses_method"  # Paper -> Method
    USES_DATASET = "uses_dataset"  # Paper -> Dataset
    DISCUSSES_CONCEPT = "discusses_concept"  # Paper -> Concept
    PUBLISHED_IN = "published_in"  # Paper -> Venue
    COLLABORATES_WITH = "collaborates_with"  # Author -> Author
    RELATED_TO = "related_to"  # Concept -> Concept
    SIMILAR_TO = "similar_to"  # Paper -> Paper (semantic similarity)


@dataclass
class NodeSchema:
    """Schema for a node in the knowledge graph"""
    node_id: str
    node_type: NodeType
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate node has required properties based on type"""
        self.properties['node_type'] = self.node_type.value
        self.properties['created_at'] = self.properties.get('created_at', datetime.now().isoformat())


@dataclass
class EdgeSchema:
    """Schema for an edge in the knowledge graph"""
    source_id: str
    target_id: str
    edge_type: EdgeType
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate edge and add metadata"""
        self.properties['edge_type'] = self.edge_type.value
        self.properties['created_at'] = self.properties.get('created_at', datetime.now().isoformat())


# Node property schemas
PAPER_PROPERTIES = {
    'required': ['title', 'paper_id'],
    'optional': [
        'abstract', 'year', 'doi', 'url', 'venue',
        'pdf_path', 'citation_count', 'full_text',
        'sections', 'references', 'embedding'
    ]
}

AUTHOR_PROPERTIES = {
    'required': ['name', 'author_id'],
    'optional': [
        'email', 'institution', 'h_index', 'citation_count',
        'research_interests', 'homepage', 'orcid'
    ]
}

CONCEPT_PROPERTIES = {
    'required': ['name', 'concept_id'],
    'optional': [
        'description', 'category', 'frequency',
        'related_terms', 'embedding'
    ]
}

METHOD_PROPERTIES = {
    'required': ['name', 'method_id'],
    'optional': [
        'description', 'category', 'parameters',
        'use_cases', 'embedding'
    ]
}

DATASET_PROPERTIES = {
    'required': ['name', 'dataset_id'],
    'optional': [
        'description', 'url', 'size', 'format',
        'domain', 'license'
    ]
}

INSTITUTION_PROPERTIES = {
    'required': ['name', 'institution_id'],
    'optional': [
        'country', 'city', 'type', 'website',
        'ranking'
    ]
}

VENUE_PROPERTIES = {
    'required': ['name', 'venue_id'],
    'optional': [
        'type', 'year', 'impact_factor', 'h5_index',
        'url', 'publisher'
    ]
}

# Edge property schemas
EDGE_PROPERTIES = {
    EdgeType.CITES: ['context', 'section', 'importance_score'],
    EdgeType.CITED_BY: ['citation_context'],
    EdgeType.AUTHORED_BY: ['author_position', 'is_corresponding'],
    EdgeType.AFFILIATED_WITH: ['start_date', 'end_date', 'position'],
    EdgeType.USES_METHOD: ['context', 'implementation_details'],
    EdgeType.USES_DATASET: ['purpose', 'preprocessing'],
    EdgeType.DISCUSSES_CONCEPT: ['frequency', 'sections', 'importance'],
    EdgeType.PUBLISHED_IN: ['pages', 'volume', 'issue'],
    EdgeType.COLLABORATES_WITH: ['num_papers', 'years'],
    EdgeType.RELATED_TO: ['similarity_score', 'relationship_type'],
    EdgeType.SIMILAR_TO: ['similarity_score', 'method']
}


def get_node_schema(node_type: NodeType) -> Dict[str, List[str]]:
    """Get property schema for a node type"""
    schemas = {
        NodeType.PAPER: PAPER_PROPERTIES,
        NodeType.AUTHOR: AUTHOR_PROPERTIES,
        NodeType.CONCEPT: CONCEPT_PROPERTIES,
        NodeType.METHOD: METHOD_PROPERTIES,
        NodeType.DATASET: DATASET_PROPERTIES,
        NodeType.INSTITUTION: INSTITUTION_PROPERTIES,
        NodeType.VENUE: VENUE_PROPERTIES
    }
    return schemas.get(node_type, {'required': ['name'], 'optional': []})


def validate_node(node: NodeSchema) -> tuple[bool, Optional[str]]:
    """
    Validate a node against its schema
    
    Returns:
        (is_valid, error_message)
    """
    schema = get_node_schema(node.node_type)
    
    # Check required properties
    for prop in schema['required']:
        if prop not in node.properties:
            return False, f"Missing required property: {prop}"
    
    return True, None


def validate_edge(edge: EdgeSchema) -> tuple[bool, Optional[str]]:
    """
    Validate an edge against its schema
    
    Returns:
        (is_valid, error_message)
    """
    # Basic validation - edges are more flexible
    if not edge.source_id or not edge.target_id:
        return False, "Edge must have source_id and target_id"
    
    return True, None


# Graph statistics schema
@dataclass
class GraphStatistics:
    """Statistics about the knowledge graph"""
    num_nodes: int = 0
    num_edges: int = 0
    node_type_counts: Dict[str, int] = field(default_factory=dict)
    edge_type_counts: Dict[str, int] = field(default_factory=dict)
    avg_degree: float = 0.0
    density: float = 0.0
    num_connected_components: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary"""
        return {
            'num_nodes': self.num_nodes,
            'num_edges': self.num_edges,
            'node_type_counts': self.node_type_counts,
            'edge_type_counts': self.edge_type_counts,
            'avg_degree': self.avg_degree,
            'density': self.density,
            'num_connected_components': self.num_connected_components
        }
