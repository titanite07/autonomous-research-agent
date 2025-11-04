"""
Citation Network Graph Builder
"""
import networkx as nx
import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class CitationNetwork:
    """Build and manage citation network graph"""
    
    def __init__(self):
        """Initialize citation network"""
        self.graph = nx.DiGraph()  # Directed graph (A cites B)
        self.papers = {}  # Paper metadata
        self.citation_map = {}  # Map citations to paper IDs
    
    def add_paper(self, paper_id: str, metadata: Dict) -> None:
        """
        Add paper to network
        
        Args:
            paper_id: Unique paper identifier
            metadata: Paper metadata (title, authors, year, etc.)
        """
        self.graph.add_node(paper_id)
        self.papers[paper_id] = metadata
        
        # Add metadata as node attributes
        for key, value in metadata.items():
            self.graph.nodes[paper_id][key] = value
        
        logger.info(f"Added paper to network: {paper_id}")
    
    def add_citation(self, 
                    citing_paper_id: str,
                    cited_paper_id: str,
                    citation_context: Optional[str] = None) -> None:
        """
        Add citation edge to network
        
        Args:
            citing_paper_id: ID of paper that cites
            cited_paper_id: ID of paper being cited
            citation_context: Optional context where citation appears
        """
        # Ensure both papers exist
        if citing_paper_id not in self.graph:
            logger.warning(f"Citing paper not in graph: {citing_paper_id}")
            self.add_paper(citing_paper_id, {'title': 'Unknown'})
        
        if cited_paper_id not in self.graph:
            logger.warning(f"Cited paper not in graph: {cited_paper_id}")
            self.add_paper(cited_paper_id, {'title': 'Unknown'})
        
        # Add edge (citing -> cited)
        self.graph.add_edge(citing_paper_id, cited_paper_id)
        
        # Store citation context as edge attribute
        if citation_context:
            if 'contexts' not in self.graph.edges[citing_paper_id, cited_paper_id]:
                self.graph.edges[citing_paper_id, cited_paper_id]['contexts'] = []
            self.graph.edges[citing_paper_id, cited_paper_id]['contexts'].append(citation_context)
        
        logger.debug(f"Added citation: {citing_paper_id} -> {cited_paper_id}")
    
    def build_from_papers(self, papers_data: List[Dict]) -> None:
        """
        Build network from list of papers with citations
        
        Args:
            papers_data: List of paper dictionaries with 'id', 'metadata', and 'citations'
        """
        # First pass: add all papers
        for paper in papers_data:
            paper_id = paper.get('id')
            metadata = paper.get('metadata', {})
            if paper_id:
                self.add_paper(paper_id, metadata)
        
        # Second pass: add citations
        for paper in papers_data:
            citing_id = paper.get('id')
            citations = paper.get('citations', [])
            
            for citation in citations:
                cited_id = citation.get('paper_id')
                context = citation.get('context')
                
                if cited_id:
                    self.add_citation(citing_id, cited_id, context)
        
        logger.info(f"Built network with {self.graph.number_of_nodes()} papers "
                   f"and {self.graph.number_of_edges()} citations")
    
    def get_citations(self, paper_id: str) -> List[str]:
        """
        Get papers cited by a paper
        
        Args:
            paper_id: Paper ID
            
        Returns:
            List of cited paper IDs
        """
        if paper_id not in self.graph:
            return []
        return list(self.graph.successors(paper_id))
    
    def get_citing_papers(self, paper_id: str) -> List[str]:
        """
        Get papers that cite a paper
        
        Args:
            paper_id: Paper ID
            
        Returns:
            List of citing paper IDs
        """
        if paper_id not in self.graph:
            return []
        return list(self.graph.predecessors(paper_id))
    
    def get_citation_count(self, paper_id: str) -> int:
        """
        Get number of times a paper is cited
        
        Args:
            paper_id: Paper ID
            
        Returns:
            Citation count
        """
        return self.graph.in_degree(paper_id)
    
    def get_reference_count(self, paper_id: str) -> int:
        """
        Get number of papers cited by a paper
        
        Args:
            paper_id: Paper ID
            
        Returns:
            Reference count
        """
        return self.graph.out_degree(paper_id)
    
    def find_common_citations(self, paper_id1: str, paper_id2: str) -> List[str]:
        """
        Find papers cited by both papers
        
        Args:
            paper_id1: First paper ID
            paper_id2: Second paper ID
            
        Returns:
            List of commonly cited paper IDs
        """
        citations1 = set(self.get_citations(paper_id1))
        citations2 = set(self.get_citations(paper_id2))
        return list(citations1 & citations2)
    
    def find_citation_path(self, 
                          source_id: str,
                          target_id: str,
                          max_length: int = 5) -> Optional[List[str]]:
        """
        Find citation path between two papers
        
        Args:
            source_id: Source paper ID
            target_id: Target paper ID
            max_length: Maximum path length
            
        Returns:
            List of paper IDs in path or None
        """
        try:
            path = nx.shortest_path(self.graph, source_id, target_id)
            if len(path) <= max_length + 1:
                return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass
        return None
    
    def get_subgraph(self, paper_ids: List[str], depth: int = 1) -> nx.DiGraph:
        """
        Get subgraph around specified papers
        
        Args:
            paper_ids: Center paper IDs
            depth: Depth of neighborhood to include
            
        Returns:
            Subgraph
        """
        nodes = set(paper_ids)
        
        for paper_id in paper_ids:
            if paper_id not in self.graph:
                continue
            
            # Add cited papers
            for _ in range(depth):
                new_nodes = set()
                for node in nodes:
                    if node in self.graph:
                        new_nodes.update(self.graph.successors(node))
                        new_nodes.update(self.graph.predecessors(node))
                nodes.update(new_nodes)
        
        return self.graph.subgraph(nodes).copy()
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Get network statistics
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            'num_papers': self.graph.number_of_nodes(),
            'num_citations': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'avg_citations_per_paper': (
                self.graph.number_of_edges() / max(1, self.graph.number_of_nodes())
            )
        }
        
        # Most cited papers
        if self.graph.number_of_nodes() > 0:
            citation_counts = [(node, self.get_citation_count(node)) 
                              for node in self.graph.nodes()]
            citation_counts.sort(key=lambda x: x[1], reverse=True)
            stats['most_cited'] = citation_counts[:10]
        
        # Connected components
        if self.graph.number_of_nodes() > 0:
            undirected = self.graph.to_undirected()
            stats['num_components'] = nx.number_connected_components(undirected)
            stats['largest_component_size'] = len(max(
                nx.connected_components(undirected),
                key=len,
                default=[]
            ))
        
        return stats
    
    def export_to_json(self, filepath: str) -> None:
        """
        Export network to JSON
        
        Args:
            filepath: Output file path
        """
        data = {
            'papers': self.papers,
            'edges': [
                {
                    'source': u,
                    'target': v,
                    'contexts': self.graph.edges[u, v].get('contexts', [])
                }
                for u, v in self.graph.edges()
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported network to {filepath}")
    
    def import_from_json(self, filepath: str) -> None:
        """
        Import network from JSON
        
        Args:
            filepath: Input file path
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Add papers
        for paper_id, metadata in data.get('papers', {}).items():
            self.add_paper(paper_id, metadata)
        
        # Add edges
        for edge in data.get('edges', []):
            source = edge['source']
            target = edge['target']
            contexts = edge.get('contexts', [])
            
            self.add_citation(source, target)
            if contexts:
                self.graph.edges[source, target]['contexts'] = contexts
        
        logger.info(f"Imported network from {filepath}")
    
    def export_to_gexf(self, filepath: str) -> None:
        """
        Export network to GEXF format (for Gephi)
        
        Args:
            filepath: Output file path
        """
        nx.write_gexf(self.graph, filepath)
        logger.info(f"Exported network to GEXF: {filepath}")
    
    def clear(self) -> None:
        """Clear the network"""
        self.graph.clear()
        self.papers.clear()
        self.citation_map.clear()
        logger.info("Cleared citation network")


# Alias for backward compatibility
CitationNetworkAnalyzer = CitationNetwork
