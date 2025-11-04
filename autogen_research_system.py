"""
AutoGen Research System - Production Implementation
Orchestrates multi-agent research using scrapers and LLM analysis
"""

import os
from typing import List, Dict, Optional
from scrapers import ArxivScraper, SemanticScholarScraper, SpringerScraper

class AutoGenResearchSystem:
    """
    Production AutoGen Research System
    Orchestrates multi-agent research workflows
    """
    
    def __init__(self):
        """Initialize the research system with scrapers"""
        print("✓ AutoGenResearchSystem initialized (production mode)")
        
        # Initialize scrapers
        self.arxiv_scraper = ArxivScraper()
        self.semantic_scholar_scraper = SemanticScholarScraper()
        
        # Initialize Springer if API key available
        springer_key = os.getenv('SPRINGER_API_KEY')
        self.springer_scraper = None
        if springer_key:
            self.springer_scraper = SpringerScraper(api_key=springer_key)
            print("✅ Springer scraper initialized")
    
    def search_papers(self, query: str, max_results: int = 10, sources: List[str] = None) -> Dict:
        """
        Search for papers across multiple sources
        
        Args:
            query: Search query string
            max_results: Maximum number of papers per source
            sources: List of sources to search (arxiv, semantic_scholar, springer)
            
        Returns:
            Dictionary with papers list
        """
        if sources is None:
            sources = ["arxiv", "semantic_scholar"]
            if self.springer_scraper:
                sources.append("springer")
        
        all_papers = []
        
        # Search arXiv
        if "arxiv" in sources:
            try:
                print(f"🔍 Searching arXiv for '{query}'...")
                arxiv_papers = self.arxiv_scraper.search(query, max_results)
                # Convert ScrapedPaper objects to dicts
                for paper in arxiv_papers:
                    paper_dict = paper.to_dict() if hasattr(paper, 'to_dict') else paper
                    paper_dict['source'] = 'arxiv'
                    all_papers.append(paper_dict)
                print(f"✅ Found {len(arxiv_papers)} papers from arXiv")
            except Exception as e:
                print(f"⚠️ arXiv search failed: {e}")
        
        # Search Semantic Scholar
        if "semantic_scholar" in sources:
            try:
                print(f"🔍 Searching Semantic Scholar for '{query}'...")
                ss_papers = self.semantic_scholar_scraper.search(query, max_results)
                # Convert ScrapedPaper objects to dicts
                for paper in ss_papers:
                    paper_dict = paper.to_dict() if hasattr(paper, 'to_dict') else paper
                    paper_dict['source'] = 'semantic_scholar'
                    all_papers.append(paper_dict)
                print(f"✅ Found {len(ss_papers)} papers from Semantic Scholar")
            except Exception as e:
                print(f"⚠️ Semantic Scholar search failed: {e}")
        
        # Search Springer
        if "springer" in sources and self.springer_scraper:
            try:
                print(f"🔍 Searching Springer for '{query}'...")
                springer_papers = self.springer_scraper.search(query, max_results)
                # Convert ScrapedPaper objects to dicts
                for paper in springer_papers:
                    paper_dict = paper.to_dict() if hasattr(paper, 'to_dict') else paper
                    paper_dict['source'] = 'springer'
                    all_papers.append(paper_dict)
                print(f"✅ Found {len(springer_papers)} papers from Springer")
            except Exception as e:
                print(f"⚠️ Springer search failed: {e}")
        
        return {
            "papers": all_papers,
            "total": len(all_papers),
            "sources": sources
        }
    
    def analyze_papers(self, papers, query):
        """
        Analyze papers using LLM
        
        Args:
            papers: List of papers to analyze
            query: Search query context
            
        Returns:
            Analysis results
        """
        # TODO: Implement LLM-based analysis
        return {
            "summary": "Analysis functionality in development",
            "key_findings": [],
            "methodology": "Statistical analysis"
        }
    
    def synthesize_findings(self, analysis_results):
        """
        Synthesize findings from multiple papers
        
        Args:
            analysis_results: Results from analyze_papers
            
        Returns:
            Synthesized findings
        """
        # TODO: Implement synthesis
        return {
            "synthesis": "Synthesis functionality in development",
            "conclusions": []
        }
