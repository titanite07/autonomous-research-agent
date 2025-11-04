"""
Knowledge Graph Builder
Constructs and manages the research paper knowledge graph
"""
import networkx as nx
import logging
from typing import List, Dict, Set, Optional, Any, Tuple
from pathlib import Path
import json

from .schema import (
    NodeType, EdgeType, NodeSchema, EdgeSchema,
    validate_node, validate_edge, GraphStatistics
)
from .entity_extractor import EntityExtractor

logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    """Build and manage knowledge graph from research papers"""
    
    def __init__(self):
        """Initialize knowledge graph builder"""
        self.graph = nx.MultiDiGraph()  # Directed graph allowing multiple edges
        self.entity_extractor = EntityExtractor()
        self.logger = logger
        
        # Track entities for deduplication
        self._node_index: Dict[str, str] = {}  # node_id -> node_type
    
    def add_paper_to_graph(
        self,
        paper_data: Dict,
        extract_entities: bool = True
    ) -> str:
        """
        Add a paper and its entities to the knowledge graph
        
        Args:
            paper_data: Paper data from Phase 2.1 extraction
            extract_entities: Whether to extract and add entities
            
        Returns:
            paper_id of the added paper
        """
        # Extract paper information
        paper_id = paper_data.get('paper_id', self._generate_paper_id(paper_data))
        
        # Create paper node
        paper_node = NodeSchema(
            node_id=paper_id,
            node_type=NodeType.PAPER,
            properties={
                'paper_id': paper_id,
                'title': paper_data.get('title', 'Unknown'),
                'abstract': paper_data.get('abstract', ''),
                'year': paper_data.get('year', ''),
                'pdf_path': paper_data.get('pdf_path', ''),
                'doi': paper_data.get('doi', ''),
            }
        )
        
        # Add full sections if available
        if 'sections' in paper_data:
            paper_node.properties['sections'] = paper_data['sections']
        
        # Add references if available
        if 'references' in paper_data:
            paper_node.properties['references'] = paper_data['references']
        
        # Add node to graph
        self._add_node(paper_node)
        
        if extract_entities:
            # Extract and add entities
            entities = self.entity_extractor.extract_all_entities(paper_data)
            
            # Add authors
            for author in entities['authors']:
                author_id = author['author_id']
                author_node = NodeSchema(
                    node_id=author_id,
                    node_type=NodeType.AUTHOR,
                    properties=author
                )
                self._add_node(author_node)
                
                # Create AUTHORED_BY edge
                self._add_edge(EdgeSchema(
                    source_id=paper_id,
                    target_id=author_id,
                    edge_type=EdgeType.AUTHORED_BY
                ))
            
            # Add concepts
            for concept in entities['concepts']:
                concept_id = concept['concept_id']
                concept_node = NodeSchema(
                    node_id=concept_id,
                    node_type=NodeType.CONCEPT,
                    properties=concept
                )
                self._add_node(concept_node)
                
                # Create DISCUSSES_CONCEPT edge
                self._add_edge(EdgeSchema(
                    source_id=paper_id,
                    target_id=concept_id,
                    edge_type=EdgeType.DISCUSSES_CONCEPT,
                    properties={'frequency': concept.get('frequency', 1)}
                ))
            
            # Add methods
            for method in entities['methods']:
                method_id = method['method_id']
                method_node = NodeSchema(
                    node_id=method_id,
                    node_type=NodeType.METHOD,
                    properties=method
                )
                self._add_node(method_node)
                
                # Create USES_METHOD edge
                self._add_edge(EdgeSchema(
                    source_id=paper_id,
                    target_id=method_id,
                    edge_type=EdgeType.USES_METHOD
                ))
            
            # Add datasets
            for dataset in entities['datasets']:
                dataset_id = dataset['dataset_id']
                dataset_node = NodeSchema(
                    node_id=dataset_id,
                    node_type=NodeType.DATASET,
                    properties=dataset
                )
                self._add_node(dataset_node)
                
                # Create USES_DATASET edge
                self._add_edge(EdgeSchema(
                    source_id=paper_id,
                    target_id=dataset_id,
                    edge_type=EdgeType.USES_DATASET
                ))
        
        self.logger.info(f"Added paper {paper_id} to knowledge graph")
        return paper_id
    
    def add_citation_edges_from_phase3(self, citation_graph: nx.DiGraph):
        """
        Import citation edges from Phase 3 citation network
        
        Args:
            citation_graph: NetworkX graph from Phase 3
        """
        edges_added = 0
        
        for source, target in citation_graph.edges():
            # Check if both papers exist in our graph
            if self.graph.has_node(source) and self.graph.has_node(target):
                self._add_edge(EdgeSchema(
                    source_id=source,
                    target_id=target,
                    edge_type=EdgeType.CITES
                ))
                edges_added += 1
        
        self.logger.info(f"Added {edges_added} citation edges from Phase 3")
    
    def build_collaboration_network(self):
        """Build author collaboration edges based on co-authorship"""
        # Get all author nodes
        authors = [
            node for node, data in self.graph.nodes(data=True)
            if data.get('node_type') == NodeType.AUTHOR.value
        ]
        
        collaborations_added = 0
        
        # For each pair of authors
        for i, author1 in enumerate(authors):
            for author2 in authors[i+1:]:
                # Find papers they co-authored
                papers1 = set(self._get_papers_by_author(author1))
                papers2 = set(self._get_papers_by_author(author2))
                common_papers = papers1 & papers2
                
                if common_papers:
                    # Add collaboration edge
                    self._add_edge(EdgeSchema(
                        source_id=author1,
                        target_id=author2,
                        edge_type=EdgeType.COLLABORATES_WITH,
                        properties={'num_papers': len(common_papers)}
                    ))
                    collaborations_added += 1
        
        self.logger.info(f"Added {collaborations_added} collaboration edges")
    
    def build_concept_relationships(self, similarity_threshold: float = 0.5):
        """Build relationships between related concepts"""
        # Get all concept nodes
        concepts = [
            (node, data) for node, data in self.graph.nodes(data=True)
            if data.get('node_type') == NodeType.CONCEPT.value
        ]
        
        relationships_added = 0
        
        # For each pair of concepts
        for i, (concept1, data1) in enumerate(concepts):
            for concept2, data2 in concepts[i+1:]:
                # Find papers discussing both concepts
                papers1 = set(self._get_papers_discussing_concept(concept1))
                papers2 = set(self._get_papers_discussing_concept(concept2))
                common_papers = papers1 & papers2
                
                if common_papers:
                    # Calculate similarity based on co-occurrence
                    similarity = len(common_papers) / min(len(papers1), len(papers2))
                    
                    if similarity >= similarity_threshold:
                        # Add related edge
                        self._add_edge(EdgeSchema(
                            source_id=concept1,
                            target_id=concept2,
                            edge_type=EdgeType.RELATED_TO,
                            properties={'similarity_score': similarity}
                        ))
                        relationships_added += 1
        
        self.logger.info(f"Added {relationships_added} concept relationship edges")
    
    def get_statistics(self) -> GraphStatistics:
        """Get statistics about the knowledge graph"""
        stats = GraphStatistics()
        
        stats.num_nodes = self.graph.number_of_nodes()
        stats.num_edges = self.graph.number_of_edges()
        
        # Count by node type
        for node, data in self.graph.nodes(data=True):
            node_type = data.get('node_type', 'unknown')
            stats.node_type_counts[node_type] = stats.node_type_counts.get(node_type, 0) + 1
        
        # Count by edge type
        for source, target, data in self.graph.edges(data=True):
            edge_type = data.get('edge_type', 'unknown')
            stats.edge_type_counts[edge_type] = stats.edge_type_counts.get(edge_type, 0) + 1
        
        # Calculate graph metrics
        if stats.num_nodes > 0:
            stats.avg_degree = sum(dict(self.graph.degree()).values()) / stats.num_nodes
            
            # Density
            max_edges = stats.num_nodes * (stats.num_nodes - 1)
            stats.density = stats.num_edges / max_edges if max_edges > 0 else 0
            
            # Connected components
            undirected = self.graph.to_undirected()
            stats.num_connected_components = nx.number_connected_components(undirected)
        
        return stats
    
    def export_to_graphml(self, output_path: Path):
        """Export knowledge graph to GraphML format"""
        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True, parents=True)
        
        # Create a copy of the graph with serialized complex attributes
        g_copy = self.graph.copy()
        
        for node, data in g_copy.nodes(data=True):
            for key, value in list(data.items()):
                if isinstance(value, (dict, list)):
                    data[key] = json.dumps(value)
        
        for source, target, key, data in g_copy.edges(data=True, keys=True):
            for attr_key, value in list(data.items()):
                if isinstance(value, (dict, list)):
                    data[attr_key] = json.dumps(value)
        
        nx.write_graphml(g_copy, str(output_path))
        self.logger.info(f"Exported knowledge graph to {output_path}")
    
    def export_to_json(self, output_path: Path):
        """Export knowledge graph to JSON format"""
        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True, parents=True)
        
        # Convert to JSON-serializable format
        data = {
            'nodes': [],
            'edges': []
        }
        
        # Export nodes
        for node, attrs in self.graph.nodes(data=True):
            node_data = {'id': node}
            node_data.update(attrs)
            data['nodes'].append(node_data)
        
        # Export edges
        for source, target, attrs in self.graph.edges(data=True):
            edge_data = {
                'source': source,
                'target': target
            }
            edge_data.update(attrs)
            data['edges'].append(edge_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Exported knowledge graph to {output_path}")
    
    # Internal helper methods
    
    def _add_node(self, node: NodeSchema):
        """Add a node to the graph (with validation and deduplication)"""
        # Validate node
        is_valid, error = validate_node(node)
        if not is_valid:
            self.logger.warning(f"Invalid node {node.node_id}: {error}")
            return
        
        # Check if node already exists
        if self.graph.has_node(node.node_id):
            # Update properties instead of creating duplicate
            existing_props = self.graph.nodes[node.node_id]
            existing_props.update(node.properties)
        else:
            # Add new node
            self.graph.add_node(node.node_id, **node.properties)
            self._node_index[node.node_id] = node.node_type.value
    
    def _add_edge(self, edge: EdgeSchema):
        """Add an edge to the graph (with validation)"""
        # Validate edge
        is_valid, error = validate_edge(edge)
        if not is_valid:
            self.logger.warning(f"Invalid edge: {error}")
            return
        
        # Add edge (MultiDiGraph allows multiple edges between same nodes)
        self.graph.add_edge(
            edge.source_id,
            edge.target_id,
            **edge.properties
        )
    
    def _generate_paper_id(self, paper_data: Dict) -> str:
        """Generate unique ID for paper"""
        if 'doi' in paper_data and paper_data['doi']:
            return f"paper_{paper_data['doi'].replace('/', '_')}"
        elif 'title' in paper_data:
            # Use first 50 chars of title
            title_slug = paper_data['title'][:50].lower().replace(' ', '_')
            return f"paper_{title_slug}"
        else:
            return f"paper_unknown_{hash(str(paper_data)) % 10000}"
    
    def _get_papers_by_author(self, author_id: str) -> List[str]:
        """Get all papers authored by a given author"""
        papers = []
        for source, target, data in self.graph.in_edges(author_id, data=True):
            if data.get('edge_type') == EdgeType.AUTHORED_BY.value:
                papers.append(source)
        return papers
    
    def _get_papers_discussing_concept(self, concept_id: str) -> List[str]:
        """Get all papers discussing a given concept"""
        papers = []
        for source, target, data in self.graph.in_edges(concept_id, data=True):
            if data.get('edge_type') == EdgeType.DISCUSSES_CONCEPT.value:
                papers.append(source)
        return papers
