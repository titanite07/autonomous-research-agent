"""
Analyze citation networks
"""
import networkx as nx
import logging
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class NetworkAnalyzer:
    """Analyze citation networks to identify patterns and important papers"""
    
    def __init__(self, citation_network):
        """
        Initialize network analyzer
        
        Args:
            citation_network: CitationNetwork instance
        """
        self.network = citation_network
        self.graph = citation_network.graph
    
    def calculate_pagerank(self, alpha: float = 0.85) -> Dict[str, float]:
        """
        Calculate PageRank scores for papers
        
        Args:
            alpha: Damping parameter
            
        Returns:
            Dictionary of paper_id -> PageRank score
        """
        if self.graph.number_of_nodes() == 0:
            return {}
        
        try:
            pagerank = nx.pagerank(self.graph, alpha=alpha)
            logger.info(f"Calculated PageRank for {len(pagerank)} papers")
            return pagerank
        except Exception as e:
            logger.error(f"Error calculating PageRank: {e}")
            return {}
    
    def calculate_centrality_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate various centrality metrics
        
        Returns:
            Dictionary of paper_id -> metrics
        """
        if self.graph.number_of_nodes() == 0:
            return {}
        
        metrics = {}
        
        try:
            # Degree centrality (in-degree = citation count)
            in_degree = dict(self.graph.in_degree())
            out_degree = dict(self.graph.out_degree())
            
            # Betweenness centrality (papers that connect different clusters)
            betweenness = nx.betweenness_centrality(self.graph)
            
            # Closeness centrality
            closeness = nx.closeness_centrality(self.graph)
            
            # Combine metrics
            for node in self.graph.nodes():
                metrics[node] = {
                    'in_degree': in_degree.get(node, 0),
                    'out_degree': out_degree.get(node, 0),
                    'betweenness': betweenness.get(node, 0),
                    'closeness': closeness.get(node, 0)
                }
            
            logger.info(f"Calculated centrality metrics for {len(metrics)} papers")
        except Exception as e:
            logger.error(f"Error calculating centrality: {e}")
        
        return metrics
    
    def identify_seminal_papers(self, 
                               top_n: int = 10,
                               min_citations: int = 5) -> List[Tuple[str, Dict]]:
        """
        Identify seminal/influential papers
        
        Args:
            top_n: Number of top papers to return
            min_citations: Minimum citation count
            
        Returns:
            List of (paper_id, metrics) tuples
        """
        if self.graph.number_of_nodes() == 0:
            return []
        
        # Calculate multiple metrics
        pagerank = self.calculate_pagerank()
        centrality = self.calculate_centrality_metrics()
        
        # Score papers by combining metrics
        paper_scores = []
        
        for paper_id in self.graph.nodes():
            citation_count = centrality.get(paper_id, {}).get('in_degree', 0)
            
            if citation_count < min_citations:
                continue
            
            # Combined score
            score = (
                pagerank.get(paper_id, 0) * 0.4 +
                centrality.get(paper_id, {}).get('betweenness', 0) * 0.3 +
                (citation_count / max(1, self.graph.number_of_nodes())) * 0.3
            )
            
            paper_scores.append((
                paper_id,
                {
                    'score': score,
                    'citations': citation_count,
                    'pagerank': pagerank.get(paper_id, 0),
                    'betweenness': centrality.get(paper_id, {}).get('betweenness', 0),
                    'metadata': self.network.papers.get(paper_id, {})
                }
            ))
        
        # Sort by score
        paper_scores.sort(key=lambda x: x[1]['score'], reverse=True)
        
        logger.info(f"Identified {len(paper_scores[:top_n])} seminal papers")
        return paper_scores[:top_n]
    
    def find_research_communities(self, 
                                 resolution: float = 1.0) -> Dict[int, List[str]]:
        """
        Detect research communities using Louvain algorithm
        
        Args:
            resolution: Resolution parameter for community detection
            
        Returns:
            Dictionary of community_id -> list of paper IDs
        """
        if self.graph.number_of_nodes() == 0:
            return {}
        
        try:
            # Convert to undirected for community detection
            undirected = self.graph.to_undirected()
            
            # Use Louvain method
            import community as community_louvain
            partition = community_louvain.best_partition(undirected, resolution=resolution)
            
            # Group by community
            communities = defaultdict(list)
            for paper_id, community_id in partition.items():
                communities[community_id].append(paper_id)
            
            logger.info(f"Found {len(communities)} research communities")
            return dict(communities)
            
        except ImportError:
            logger.warning("python-louvain not installed, using connected components instead")
            # Fallback to connected components
            undirected = self.graph.to_undirected()
            components = list(nx.connected_components(undirected))
            
            communities = {i: list(comp) for i, comp in enumerate(components)}
            logger.info(f"Found {len(communities)} connected components")
            return communities
        
        except Exception as e:
            logger.error(f"Error detecting communities: {e}")
            return {}
    
    def analyze_temporal_patterns(self) -> Dict[str, any]:
        """
        Analyze citation patterns over time
        
        Returns:
            Dictionary with temporal analysis
        """
        if self.graph.number_of_nodes() == 0:
            return {}
        
        # Extract years from paper metadata
        papers_by_year = defaultdict(list)
        citations_by_year = defaultdict(int)
        
        for paper_id, metadata in self.network.papers.items():
            year = metadata.get('year')
            if year:
                papers_by_year[year].append(paper_id)
        
        # Count citations for each year
        for source, target in self.graph.edges():
            source_year = self.network.papers.get(source, {}).get('year')
            target_year = self.network.papers.get(target, {}).get('year')
            
            if source_year and target_year:
                # Citation from source_year to target_year
                citations_by_year[source_year] += 1
        
        # Calculate statistics
        years = sorted(papers_by_year.keys())
        
        analysis = {
            'years': years,
            'papers_per_year': {year: len(papers) for year, papers in papers_by_year.items()},
            'citations_per_year': dict(citations_by_year),
            'total_papers': sum(len(papers) for papers in papers_by_year.values())
        }
        
        # Find most influential years
        if citations_by_year:
            most_influential = max(citations_by_year.items(), key=lambda x: x[1])
            analysis['most_influential_year'] = most_influential[0]
            analysis['most_influential_year_citations'] = most_influential[1]
        
        logger.info(f"Analyzed temporal patterns across {len(years)} years")
        return analysis
    
    def find_citation_gaps(self, paper_id: str, depth: int = 2) -> List[str]:
        """
        Find potentially missing citations by analyzing the citation neighborhood
        
        Args:
            paper_id: Paper to analyze
            depth: Depth of search
            
        Returns:
            List of paper IDs that might be missing citations
        """
        if paper_id not in self.graph:
            return []
        
        # Get papers cited by this paper
        direct_citations = set(self.network.get_citations(paper_id))
        
        # Get papers cited by the cited papers (second-order citations)
        second_order = set()
        for cited_id in direct_citations:
            second_order.update(self.network.get_citations(cited_id))
        
        # Find papers that are heavily cited by our citations but not by us
        gap_candidates = []
        for candidate in second_order:
            if candidate == paper_id:
                continue
            if candidate in direct_citations:
                continue
            
            # Count how many of our citations cite this candidate
            count = sum(1 for cited in direct_citations 
                       if candidate in self.network.get_citations(cited))
            
            if count >= 2:  # Cited by at least 2 of our citations
                gap_candidates.append((candidate, count))
        
        # Sort by frequency
        gap_candidates.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Found {len(gap_candidates)} potential citation gaps for {paper_id}")
        return [paper_id for paper_id, _ in gap_candidates]
    
    def get_co_citation_analysis(self, min_co_citations: int = 2) -> List[Tuple[str, str, int]]:
        """
        Find papers frequently co-cited together
        
        Args:
            min_co_citations: Minimum number of co-citations
            
        Returns:
            List of (paper1_id, paper2_id, co_citation_count) tuples
        """
        # Build co-citation matrix
        co_citations = defaultdict(int)
        
        for paper_id in self.graph.nodes():
            citations = self.network.get_citations(paper_id)
            
            # Count all pairs of citations
            for i, cite1 in enumerate(citations):
                for cite2 in citations[i+1:]:
                    pair = tuple(sorted([cite1, cite2]))
                    co_citations[pair] += 1
        
        # Filter and sort
        result = [
            (p1, p2, count)
            for (p1, p2), count in co_citations.items()
            if count >= min_co_citations
        ]
        result.sort(key=lambda x: x[2], reverse=True)
        
        logger.info(f"Found {len(result)} co-citation pairs")
        return result
    
    def get_comprehensive_analysis(self) -> Dict[str, any]:
        """
        Get comprehensive network analysis
        
        Returns:
            Dictionary with all analysis results
        """
        logger.info("Starting comprehensive network analysis...")
        
        analysis = {
            'statistics': self.network.get_statistics(),
            'seminal_papers': self.identify_seminal_papers(top_n=20),
            'communities': self.find_research_communities(),
            'temporal_patterns': self.analyze_temporal_patterns(),
            'pagerank': self.calculate_pagerank(),
            'centrality': self.calculate_centrality_metrics(),
            'co_citations': self.get_co_citation_analysis()[:50]  # Top 50
        }
        
        logger.info("Comprehensive analysis complete")
        return analysis
