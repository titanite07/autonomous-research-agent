"""
Knowledge Graph Query Interface
Provides powerful querying capabilities for the research knowledge graph
"""
import networkx as nx
import logging
from typing import List, Dict, Optional, Set, Tuple, Any
from collections import defaultdict

from .schema import NodeType, EdgeType

logger = logging.getLogger(__name__)


class KnowledgeGraphQuery:
    """Query interface for knowledge graph"""
    
    def __init__(self, graph: nx.MultiDiGraph):
        """
        Initialize query interface
        
        Args:
            graph: Knowledge graph (NetworkX MultiDiGraph)
        """
        self.graph = graph
        self.logger = logger
    
    # Paper Queries
    
    def find_papers_by_author(self, author_name: str) -> List[Dict]:
        """Find all papers by a given author"""
        papers = []
        
        # Find author node
        author_id = f"author_{author_name.lower().replace(' ', '_')}"
        if not self.graph.has_node(author_id):
            return []
        
        # Find papers with AUTHORED_BY edge
        for source, target, data in self.graph.in_edges(author_id, data=True):
            if data.get('edge_type') == EdgeType.AUTHORED_BY.value:
                paper_data = self.graph.nodes[source]
                papers.append({'paper_id': source, **paper_data})
        
        return papers
    
    def find_papers_by_concept(self, concept: str, min_frequency: int = 1) -> List[Dict]:
        """Find papers discussing a specific concept"""
        papers = []
        
        concept_id = f"concept_{concept.lower().replace(' ', '_')}"
        if not self.graph.has_node(concept_id):
            return []
        
        # Find papers with DISCUSSES_CONCEPT edge
        for source, target, data in self.graph.in_edges(concept_id, data=True):
            if data.get('edge_type') == EdgeType.DISCUSSES_CONCEPT.value:
                frequency = data.get('frequency', 1)
                if frequency >= min_frequency:
                    paper_data = self.graph.nodes[source]
                    papers.append({
                        'paper_id': source,
                        'concept_frequency': frequency,
                        **paper_data
                    })
        
        # Sort by frequency
        papers.sort(key=lambda x: x.get('concept_frequency', 0), reverse=True)
        return papers
    
    def find_papers_by_method(self, method: str) -> List[Dict]:
        """Find papers using a specific method"""
        papers = []
        
        method_id = f"method_{method.lower().replace(' ', '_')}"
        if not self.graph.has_node(method_id):
            return []
        
        for source, target, data in self.graph.in_edges(method_id, data=True):
            if data.get('edge_type') == EdgeType.USES_METHOD.value:
                paper_data = self.graph.nodes[source]
                papers.append({'paper_id': source, **paper_data})
        
        return papers
    
    def find_papers_by_dataset(self, dataset: str) -> List[Dict]:
        """Find papers using a specific dataset"""
        papers = []
        
        dataset_id = f"dataset_{dataset.lower().replace(' ', '_')}"
        if not self.graph.has_node(dataset_id):
            return []
        
        for source, target, data in self.graph.in_edges(dataset_id, data=True):
            if data.get('edge_type') == EdgeType.USES_DATASET.value:
                paper_data = self.graph.nodes[source]
                papers.append({'paper_id': source, **paper_data})
        
        return papers
    
    def find_related_papers(
        self,
        paper_id: str,
        max_depth: int = 2,
        relation_types: Optional[List[EdgeType]] = None
    ) -> List[Dict]:
        """
        Find papers related to a given paper
        
        Args:
            paper_id: Source paper ID
            max_depth: Maximum path length
            relation_types: Types of relations to follow (default: CITES, SIMILAR_TO)
        """
        if not self.graph.has_node(paper_id):
            return []
        
        if relation_types is None:
            relation_types = [EdgeType.CITES, EdgeType.SIMILAR_TO]
        relation_type_values = [rt.value for rt in relation_types]
        
        related = []
        visited = {paper_id}
        
        # BFS to find related papers
        queue = [(paper_id, 0)]
        
        while queue:
            current, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
            
            # Check outgoing edges
            for source, target, data in self.graph.out_edges(current, data=True):
                edge_type = data.get('edge_type')
                if edge_type in relation_type_values and target not in visited:
                    if self.graph.nodes[target].get('node_type') == NodeType.PAPER.value:
                        paper_data = self.graph.nodes[target]
                        related.append({
                            'paper_id': target,
                            'relation': edge_type,
                            'depth': depth + 1,
                            **paper_data
                        })
                        visited.add(target)
                        queue.append((target, depth + 1))
        
        return related
    
    # Author Queries
    
    def get_author_collaboration_network(self, author_name: str) -> Dict:
        """Get collaboration network for an author"""
        author_id = f"author_{author_name.lower().replace(' ', '_')}"
        if not self.graph.has_node(author_id):
            return {'author': author_name, 'num_collaborators': 0, 'collaborators': []}
        
        collaborators = []
        
        # Find direct collaborators
        for source, target, data in self.graph.out_edges(author_id, data=True):
            if data.get('edge_type') == EdgeType.COLLABORATES_WITH.value:
                collab_data = self.graph.nodes[target]
                collaborators.append({
                    'author_id': target,
                    'name': collab_data.get('name', 'Unknown'),
                    'num_papers': data.get('num_papers', 0)
                })
        
        return {
            'author': author_name,
            'author_id': author_id,
            'num_collaborators': len(collaborators),
            'collaborators': collaborators
        }
    
    def get_most_prolific_authors(self, top_n: int = 10) -> List[Dict]:
        """Get authors with most papers"""
        author_papers = defaultdict(int)
        
        # Count papers for each author
        for source, target, data in self.graph.edges(data=True):
            if data.get('edge_type') == EdgeType.AUTHORED_BY.value:
                author_papers[target] += 1
        
        # Sort by paper count
        sorted_authors = sorted(
            author_papers.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        result = []
        for author_id, paper_count in sorted_authors:
            author_data = self.graph.nodes[author_id]
            result.append({
                'author_id': author_id,
                'name': author_data.get('name', 'Unknown'),
                'paper_count': paper_count
            })
        
        return result
    
    # Concept Queries
    
    def get_trending_concepts(self, top_n: int = 20) -> List[Dict]:
        """Get most discussed concepts"""
        concept_freq = defaultdict(int)
        
        # Sum frequencies for each concept
        for source, target, data in self.graph.edges(data=True):
            if data.get('edge_type') == EdgeType.DISCUSSES_CONCEPT.value:
                concept_freq[target] += data.get('frequency', 1)
        
        # Sort by frequency
        sorted_concepts = sorted(
            concept_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        result = []
        for concept_id, total_freq in sorted_concepts:
            concept_data = self.graph.nodes[concept_id]
            result.append({
                'concept_id': concept_id,
                'name': concept_data.get('name', 'Unknown'),
                'total_frequency': total_freq,
                'category': concept_data.get('category', 'general')
            })
        
        return result
    
    def get_related_concepts(self, concept: str, similarity_threshold: float = 0.3) -> List[Dict]:
        """Find concepts related to a given concept"""
        concept_id = f"concept_{concept.lower().replace(' ', '_')}"
        if not self.graph.has_node(concept_id):
            return []
        
        related = []
        
        # Find concepts with RELATED_TO edge
        for source, target, data in self.graph.out_edges(concept_id, data=True):
            if data.get('edge_type') == EdgeType.RELATED_TO.value:
                similarity = data.get('similarity_score', 0)
                if similarity >= similarity_threshold:
                    concept_data = self.graph.nodes[target]
                    related.append({
                        'concept_id': target,
                        'name': concept_data.get('name', 'Unknown'),
                        'similarity_score': similarity
                    })
        
        # Sort by similarity
        related.sort(key=lambda x: x['similarity_score'], reverse=True)
        return related
    
    # Citation Analysis
    
    def get_most_cited_papers(self, top_n: int = 10) -> List[Dict]:
        """Get papers with most citations"""
        citation_counts = defaultdict(int)
        
        # Count incoming citations
        for source, target, data in self.graph.edges(data=True):
            if data.get('edge_type') == EdgeType.CITES.value:
                citation_counts[target] += 1
        
        # Sort by citation count
        sorted_papers = sorted(
            citation_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        result = []
        for paper_id, cite_count in sorted_papers:
            paper_data = self.graph.nodes[paper_id]
            result.append({
                'paper_id': paper_id,
                'title': paper_data.get('title', 'Unknown'),
                'citation_count': cite_count
            })
        
        return result
    
    def get_citation_chain(self, paper_id: str, max_depth: int = 3) -> List[List[str]]:
        """Get citation chains from a paper"""
        if not self.graph.has_node(paper_id):
            return []
        
        chains = []
        
        def dfs_citations(current: str, path: List[str], depth: int):
            if depth >= max_depth:
                if len(path) > 1:
                    chains.append(path.copy())
                return
            
            # Find papers cited by current paper
            for source, target, data in self.graph.out_edges(current, data=True):
                if data.get('edge_type') == EdgeType.CITES.value:
                    if target not in path:  # Avoid cycles
                        path.append(target)
                        dfs_citations(target, path, depth + 1)
                        path.pop()
            
            if len(path) > 1:
                chains.append(path.copy())
        
        dfs_citations(paper_id, [paper_id], 0)
        return chains
    
    # Graph Analysis
    
    def find_shortest_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find shortest path between two nodes"""
        try:
            path = nx.shortest_path(self.graph, source_id, target_id)
            return path
        except nx.NetworkXNoPath:
            return None
    
    def get_subgraph_by_concept(self, concept: str) -> nx.MultiDiGraph:
        """Extract subgraph containing papers and entities related to a concept"""
        concept_id = f"concept_{concept.lower().replace(' ', '_')}"
        if not self.graph.has_node(concept_id):
            return nx.MultiDiGraph()
        
        # Start with concept node
        nodes_to_include = {concept_id}
        
        # Add papers discussing this concept
        for source, target, data in self.graph.in_edges(concept_id, data=True):
            if data.get('edge_type') == EdgeType.DISCUSSES_CONCEPT.value:
                nodes_to_include.add(source)
                
                # Add all entities connected to these papers
                for s, t, d in self.graph.out_edges(source, data=True):
                    nodes_to_include.add(t)
        
        # Extract subgraph
        return self.graph.subgraph(nodes_to_include).copy()
    
    def get_node_details(self, node_id: str) -> Optional[Dict]:
        """Get detailed information about a node"""
        if not self.graph.has_node(node_id):
            return None
        
        node_data = dict(self.graph.nodes[node_id])
        
        # Add edge information
        in_edges = list(self.graph.in_edges(node_id, data=True))
        out_edges = list(self.graph.out_edges(node_id, data=True))
        
        node_data['in_degree'] = len(in_edges)
        node_data['out_degree'] = len(out_edges)
        
        return node_data
