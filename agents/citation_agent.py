"""
Citation Agent - Manages references, citation networks, and bibliographies
"""
from typing import Dict, List, Optional, Set
import logging
import re
from datetime import datetime
import networkx as nx

logger = logging.getLogger(__name__)


class CitationAgent:
    """Agent responsible for citation tracking and bibliography generation"""
    
    def __init__(self):
        """Initialize CitationAgent"""
        self.citation_graph = nx.DiGraph()
        self.papers_db = {}
        
        logger.info("CitationAgent initialized")
    
    def _paper_to_dict(self, paper) -> Dict:
        """
        Convert Paper object to dictionary if needed
        
        Args:
            paper: Paper object or dictionary
            
        Returns:
            Dictionary representation
        """
        if hasattr(paper, 'to_dict'):
            return paper.to_dict()
        elif isinstance(paper, dict):
            return paper
        else:
            # Fallback for unknown types
            return {
                'paper_id': str(getattr(paper, 'paper_id', '')),
                'title': str(getattr(paper, 'title', '')),
                'authors': getattr(paper, 'authors', []),
                'abstract': str(getattr(paper, 'abstract', '')),
                'url': str(getattr(paper, 'url', '')),
                'published_date': getattr(paper, 'published_date', ''),
                'citations': getattr(paper, 'citations', 0),
                'source': str(getattr(paper, 'source', 'unknown'))
            }
    
    def add_paper(self, paper) -> None:
        """
        Add paper to citation database
        
        Args:
            paper: Paper object or dictionary with metadata
        """
        paper_dict = self._paper_to_dict(paper)
        paper_id = paper_dict.get("paper_id", "")
        if not paper_id:
            logger.warning("Paper missing ID, skipping")
            return
        
        self.papers_db[paper_id] = paper_dict
        self.citation_graph.add_node(paper_id, **paper_dict)
        
        logger.debug(f"Added paper: {paper_id}")
    
    def add_citation(self, citing_paper_id: str, cited_paper_id: str) -> None:
        """
        Add citation relationship
        
        Args:
            citing_paper_id: ID of paper that cites
            cited_paper_id: ID of paper being cited
        """
        self.citation_graph.add_edge(citing_paper_id, cited_paper_id)
        logger.debug(f"Added citation: {citing_paper_id} -> {cited_paper_id}")
    
    def build_citation_network(self, papers: List) -> nx.DiGraph:
        """
        Build citation network from papers
        
        Args:
            papers: List of Paper objects or dictionaries
            
        Returns:
            NetworkX directed graph
        """
        logger.info(f"Building citation network from {len(papers)} papers")
        
        for paper in papers:
            self.add_paper(paper)
        
        logger.info(f"Citation network built with {self.citation_graph.number_of_nodes()} nodes")
        
        return self.citation_graph
    
    def get_most_cited(self, top_n: int = 10) -> List[Dict]:
        """
        Get most cited papers
        
        Args:
            top_n: Number of papers to return
            
        Returns:
            List of papers sorted by citation count
        """
        citation_counts = dict(self.citation_graph.in_degree())
        sorted_papers = sorted(citation_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        result = []
        for paper_id, citation_count in sorted_papers:
            if paper_id in self.papers_db:
                paper_info = self.papers_db[paper_id].copy()
                paper_info["citation_count"] = citation_count
                result.append(paper_info)
        
        logger.info(f"Retrieved {len(result)} most cited papers")
        
        return result
    
    def get_citation_chain(self, paper_id: str) -> List[str]:
        """
        Get citation chain for a paper
        
        Args:
            paper_id: Paper ID
            
        Returns:
            List of paper IDs in citation chain
        """
        if paper_id not in self.citation_graph:
            return []
        
        # Get all papers cited by this paper
        cited_papers = list(self.citation_graph.successors(paper_id))
        
        return cited_papers
    
    def format_citation(self, paper, style: str = "APA") -> str:
        """
        Format citation in specified style
        
        Args:
            paper: Paper object or dictionary
            style: Citation style (APA, MLA, Chicago, IEEE, Harvard)
            
        Returns:
            Formatted citation string
        """
        paper_dict = self._paper_to_dict(paper)
        style = style.upper()
        
        if style == "APA":
            return self._format_apa(paper_dict)
        elif style == "MLA":
            return self._format_mla(paper_dict)
        elif style == "CHICAGO":
            return self._format_chicago(paper_dict)
        elif style == "IEEE":
            return self._format_ieee(paper_dict)
        elif style == "HARVARD":
            return self._format_harvard(paper_dict)
        else:
            logger.warning(f"Unknown citation style: {style}, defaulting to APA")
            return self._format_apa(paper_dict)
    
    def _format_apa(self, paper: Dict) -> str:
        """Format citation in APA style"""
        authors = paper.get("authors", [])
        title = paper.get("title", "")
        year = self._extract_year(paper.get("published_date", ""))
        url = paper.get("url", "")
        
        # Format authors (APA style)
        if len(authors) == 0:
            author_str = "Unknown"
        elif len(authors) == 1:
            author_str = self._format_author_apa(authors[0])
        elif len(authors) == 2:
            author_str = f"{self._format_author_apa(authors[0])} & {self._format_author_apa(authors[1])}"
        elif len(authors) <= 20:
            author_str = ", ".join([self._format_author_apa(a) for a in authors[:-1]])
            author_str += f", & {self._format_author_apa(authors[-1])}"
        else:
            # More than 20 authors: list first 19, then "..." then last author
            author_str = ", ".join([self._format_author_apa(a) for a in authors[:19]])
            author_str += f", ... {self._format_author_apa(authors[-1])}"
        
        citation = f"{author_str} ({year}). {title}. "
        
        # Add source info
        source = paper.get("source", "arXiv")
        if source == "arXiv":
            citation += f"arXiv preprint. {url}"
        else:
            citation += f"Retrieved from {url}"
        
        return citation
    
    def _format_mla(self, paper: Dict) -> str:
        """Format citation in MLA style"""
        authors = paper.get("authors", [])
        title = paper.get("title", "")
        year = self._extract_year(paper.get("published_date", ""))
        url = paper.get("url", "")
        
        # Format authors (MLA style)
        if len(authors) == 0:
            author_str = "Unknown"
        elif len(authors) == 1:
            author_str = self._format_author_mla(authors[0])
        elif len(authors) == 2:
            author_str = f"{self._format_author_mla(authors[0])} and {self._format_author_mla(authors[1])}"
        else:
            author_str = f"{self._format_author_mla(authors[0])}, et al."
        
        citation = f'{author_str}. "{title}." {year}. Web. {url}'
        
        return citation
    
    def _format_chicago(self, paper: Dict) -> str:
        """Format citation in Chicago style"""
        authors = paper.get("authors", [])
        title = paper.get("title", "")
        year = self._extract_year(paper.get("published_date", ""))
        url = paper.get("url", "")
        
        # Format authors
        if len(authors) == 0:
            author_str = "Unknown"
        elif len(authors) <= 3:
            author_str = ", ".join([self._format_author_chicago(a) for a in authors])
        else:
            author_str = f"{self._format_author_chicago(authors[0])}, et al."
        
        citation = f'{author_str}. "{title}." {year}. {url}.'
        
        return citation
    
    def _format_ieee(self, paper: Dict) -> str:
        """Format citation in IEEE style"""
        authors = paper.get("authors", [])
        title = paper.get("title", "")
        year = self._extract_year(paper.get("published_date", ""))
        url = paper.get("url", "")
        
        # Format authors (IEEE style: initials first)
        if len(authors) == 0:
            author_str = "Unknown"
        elif len(authors) <= 6:
            author_str = ", ".join([self._format_author_ieee(a) for a in authors])
        else:
            author_str = f"{self._format_author_ieee(authors[0])}, et al."
        
        citation = f'{author_str}, "{title}," {year}. [Online]. Available: {url}'
        
        return citation
    
    def _format_harvard(self, paper: Dict) -> str:
        """Format citation in Harvard style"""
        authors = paper.get("authors", [])
        title = paper.get("title", "")
        year = self._extract_year(paper.get("published_date", ""))
        url = paper.get("url", "")
        
        # Format authors
        if len(authors) == 0:
            author_str = "Unknown"
        elif len(authors) <= 3:
            author_str = " and ".join([self._format_author_harvard(a) for a in authors])
        else:
            author_str = f"{self._format_author_harvard(authors[0])} et al."
        
        citation = f"{author_str} ({year}) '{title}'. Available at: {url} (Accessed: {datetime.now().strftime('%d %B %Y')})."
        
        return citation
    
    def _format_author_apa(self, author: str) -> str:
        """Format author name for APA (Last, F. M.)"""
        parts = author.strip().split()
        if len(parts) == 0:
            return "Unknown"
        elif len(parts) == 1:
            return parts[0]
        else:
            last_name = parts[-1]
            initials = " ".join([f"{p[0]}." for p in parts[:-1] if p])
            return f"{last_name}, {initials}"
    
    def _format_author_mla(self, author: str) -> str:
        """Format author name for MLA (Last, First)"""
        parts = author.strip().split()
        if len(parts) <= 1:
            return author
        return f"{parts[-1]}, {' '.join(parts[:-1])}"
    
    def _format_author_chicago(self, author: str) -> str:
        """Format author name for Chicago (Last, First)"""
        return self._format_author_mla(author)
    
    def _format_author_ieee(self, author: str) -> str:
        """Format author name for IEEE (F. M. Last)"""
        parts = author.strip().split()
        if len(parts) <= 1:
            return author
        
        initials = " ".join([f"{p[0]}." for p in parts[:-1] if p])
        last_name = parts[-1]
        return f"{initials} {last_name}"
    
    def _format_author_harvard(self, author: str) -> str:
        """Format author name for Harvard (Last, F.M.)"""
        parts = author.strip().split()
        if len(parts) <= 1:
            return author
        
        last_name = parts[-1]
        initials = "".join([f"{p[0]}." for p in parts[:-1] if p])
        return f"{last_name}, {initials}"
    
    def _extract_year(self, date_str: str) -> str:
        """Extract year from date string"""
        if not date_str:
            return "n.d."
        
        # Try to extract year using regex
        year_match = re.search(r'\b(19|20)\d{2}\b', str(date_str))
        if year_match:
            return year_match.group(0)
        
        return "n.d."
    
    def generate_bibliography(self, papers: List[Dict], style: str = "APA") -> List[str]:
        """
        Generate bibliography for list of papers
        
        Args:
            papers: List of paper dictionaries
            style: Citation style
            
        Returns:
            List of formatted citations
        """
        logger.info(f"Generating bibliography in {style} style for {len(papers)} papers")
        
        citations = []
        for paper in papers:
            citation = self.format_citation(paper, style)
            citations.append(citation)
        
        # Sort alphabetically by first author's last name
        citations.sort()
        
        return citations
    
    def get_network_stats(self) -> Dict:
        """
        Get statistics about the citation network
        
        Returns:
            Dictionary with network statistics
        """
        stats = {
            "total_papers": self.citation_graph.number_of_nodes(),
            "total_citations": self.citation_graph.number_of_edges(),
            "avg_citations_per_paper": 0,
            "most_cited_paper": None,
            "network_density": 0
        }
        
        if stats["total_papers"] > 0:
            stats["avg_citations_per_paper"] = stats["total_citations"] / stats["total_papers"]
            
            # Get most cited paper
            citation_counts = dict(self.citation_graph.in_degree())
            if citation_counts:
                most_cited_id = max(citation_counts, key=citation_counts.get)
                stats["most_cited_paper"] = self.papers_db.get(most_cited_id, {}).get("title", "Unknown")
                stats["max_citations"] = citation_counts[most_cited_id]
            
            # Network density
            if stats["total_papers"] > 1:
                max_edges = stats["total_papers"] * (stats["total_papers"] - 1)
                stats["network_density"] = stats["total_citations"] / max_edges if max_edges > 0 else 0
        
        logger.info(f"Network stats: {stats['total_papers']} papers, {stats['total_citations']} citations")
        
        return stats
    
    def export_network(self, format: str = "json") -> str:
        """
        Export citation network
        
        Args:
            format: Export format (json, gml, graphml)
            
        Returns:
            Serialized network data
        """
        if format == "json":
            from networkx.readwrite import json_graph
            data = json_graph.node_link_data(self.citation_graph)
            import json
            return json.dumps(data, indent=2)
        elif format == "gml":
            return "\n".join(nx.generate_gml(self.citation_graph))
        elif format == "graphml":
            import io
            buffer = io.StringIO()
            nx.write_graphml(self.citation_graph, buffer)
            return buffer.getvalue()
        else:
            logger.warning(f"Unknown export format: {format}")
            return ""
