"""
Analyzer Agent
Analyzes research papers using knowledge graph and NLP
"""
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .base_agent import BaseAgent, AgentRole, Task
from core.knowledge_graph import (
    KnowledgeGraphBuilder,
    KnowledgeGraphQuery,
    EntityExtractor
)
from core.citations.citation_network import CitationNetworkAnalyzer


logger = logging.getLogger(__name__)


class AnalyzerAgent(BaseAgent):
    """
    Analyzer Agent: Analyzes research papers
    
    Responsibilities:
    - Extract entities from papers (authors, concepts, methods)
    - Build knowledge graph from papers
    - Analyze citation networks
    - Identify trends and patterns
    - Generate insights
    """
    
    def __init__(
        self,
        agent_id: str = "analyzer",
        llm_config: Optional[Dict] = None
    ):
        """
        Initialize Analyzer Agent
        
        Args:
            agent_id: Agent identifier
            llm_config: LLM configuration
        """
        super().__init__(agent_id, AgentRole.ANALYZER, llm_config)
        
        # Initialize analysis tools
        self.kg_builder = KnowledgeGraphBuilder()
        self.entity_extractor = EntityExtractor()
        self.citation_analyzer = CitationNetworkAnalyzer()
        
        # Analysis results cache
        self.analysis_cache: Dict[str, Dict] = {}
        
        self.logger.info("Analyzer Agent initialized")
    
    async def process_task(self, task: Task) -> Any:
        """
        Process analysis tasks
        
        Args:
            task: Task to process
            
        Returns:
            Task result
        """
        if task.task_type == "analyze_papers":
            return await self._analyze_papers(task)
        elif task.task_type == "extract_entities":
            return await self._extract_entities(task)
        elif task.task_type == "build_knowledge_graph":
            return await self._build_knowledge_graph(task)
        elif task.task_type == "analyze_citations":
            return await self._analyze_citations(task)
        else:
            raise ValueError(f"Unknown task type: {task.task_type}")
    
    async def _analyze_papers(self, task: Task) -> Dict:
        """
        Comprehensive paper analysis
        
        Args:
            task: Analysis task
            
        Returns:
            Analysis results
        """
        papers = task.parameters.get('papers', [])
        query = task.parameters.get('query', '')
        
        self.logger.info(f"Analyzing {len(papers)} papers for query: {query}")
        
        # Extract entities from all papers
        all_entities = {
            'authors': [],
            'concepts': [],
            'methods': [],
            'datasets': []
        }
        
        for paper in papers:
            entities = self.entity_extractor.extract_all_entities(paper)
            for key in all_entities:
                all_entities[key].extend(entities[key])
        
        # Build knowledge graph
        for paper in papers:
            self.kg_builder.add_paper_to_graph(paper, extract_entities=True)
        
        # Get graph statistics
        kg_stats = self.kg_builder.get_statistics()
        
        # Query interface for insights
        kg_query = KnowledgeGraphQuery(self.kg_builder.graph)
        
        # Get trending concepts
        trending_concepts = kg_query.get_trending_concepts(top_n=10)
        
        # Get most prolific authors
        top_authors = kg_query.get_most_prolific_authors(top_n=10)
        
        # Analyze citations if available
        citation_analysis = None
        if any('references' in p for p in papers):
            citation_analysis = await self._analyze_paper_citations(papers)
        
        # Generate insights
        insights = self._generate_insights(
            papers,
            all_entities,
            trending_concepts,
            top_authors,
            citation_analysis
        )
        
        analysis_result = {
            'query': query,
            'total_papers': len(papers),
            'entity_summary': {
                'total_authors': len(all_entities['authors']),
                'total_concepts': len(all_entities['concepts']),
                'total_methods': len(all_entities['methods']),
                'total_datasets': len(all_entities['datasets'])
            },
            'knowledge_graph': {
                'nodes': kg_stats.num_nodes,
                'edges': kg_stats.num_edges,
                'density': kg_stats.density
            },
            'trending_concepts': trending_concepts[:5],
            'top_authors': top_authors[:5],
            'citation_analysis': citation_analysis,
            'insights': insights
        }
        
        # Cache results
        self.analysis_cache[query] = analysis_result
        self.memory.store_long_term(f"analysis_{query}", analysis_result)
        
        self.logger.info(f"Analysis completed for query: {query}")
        
        return analysis_result
    
    async def _extract_entities(self, task: Task) -> Dict:
        """
        Extract entities from papers
        
        Args:
            task: Extraction task
            
        Returns:
            Extracted entities
        """
        papers = task.parameters.get('papers', [])
        
        self.logger.info(f"Extracting entities from {len(papers)} papers")
        
        all_entities = {
            'authors': [],
            'concepts': [],
            'methods': [],
            'datasets': []
        }
        
        for paper in papers:
            entities = self.entity_extractor.extract_all_entities(paper)
            for key in all_entities:
                all_entities[key].extend(entities[key])
        
        return all_entities
    
    async def _build_knowledge_graph(self, task: Task) -> Dict:
        """
        Build knowledge graph from papers
        
        Args:
            task: Graph building task
            
        Returns:
            Graph statistics
        """
        papers = task.parameters.get('papers', [])
        
        self.logger.info(f"Building knowledge graph from {len(papers)} papers")
        
        for paper in papers:
            self.kg_builder.add_paper_to_graph(paper, extract_entities=True)
        
        # Build relationships
        self.kg_builder.build_collaboration_network()
        self.kg_builder.build_concept_relationships()
        
        stats = self.kg_builder.get_statistics()
        
        return {
            'total_nodes': stats.num_nodes,
            'total_edges': stats.num_edges,
            'node_types': stats.node_type_counts,
            'edge_types': stats.edge_type_counts,
            'density': stats.density
        }
    
    async def _analyze_citations(self, task: Task) -> Dict:
        """
        Analyze citation network
        
        Args:
            task: Citation analysis task
            
        Returns:
            Citation analysis results
        """
        papers = task.parameters.get('papers', [])
        
        return await self._analyze_paper_citations(papers)
    
    async def _analyze_paper_citations(self, papers: List[Dict]) -> Dict:
        """
        Analyze citations in papers
        
        Args:
            papers: List of papers
            
        Returns:
            Citation analysis
        """
        self.logger.info(f"Analyzing citations in {len(papers)} papers")
        
        # Build citation network
        for paper in papers:
            if 'references' in paper:
                paper_id = paper.get('paper_id', paper.get('title', ''))
                references = paper['references']
                
                self.citation_analyzer.add_paper(paper_id, references)
        
        # Analyze network
        metrics = self.citation_analyzer.calculate_metrics()
        most_cited = self.citation_analyzer.get_most_cited_papers(top_n=10)
        influential = self.citation_analyzer.get_most_influential_papers(top_n=10)
        
        return {
            'total_papers': metrics.get('num_papers', 0),
            'total_citations': metrics.get('num_citations', 0),
            'most_cited_papers': most_cited[:5],
            'influential_papers': influential[:5],
            'network_density': metrics.get('density', 0)
        }
    
    def _generate_insights(
        self,
        papers: List[Dict],
        entities: Dict,
        trending_concepts: List[Dict],
        top_authors: List[Dict],
        citation_analysis: Optional[Dict]
    ) -> List[str]:
        """
        Generate insights from analysis
        
        Args:
            papers: Analyzed papers
            entities: Extracted entities
            trending_concepts: Trending concepts
            top_authors: Top authors
            citation_analysis: Citation analysis results
            
        Returns:
            List of insights
        """
        insights = []
        
        # Insight 1: Paper volume
        insights.append(f"Analyzed {len(papers)} research papers on this topic.")
        
        # Insight 2: Top concepts
        if trending_concepts:
            top_3_concepts = [c['name'] for c in trending_concepts[:3]]
            insights.append(
                f"Most discussed concepts: {', '.join(top_3_concepts)}"
            )
        
        # Insight 3: Top authors
        if top_authors:
            top_3_authors = [a['name'] for a in top_authors[:3]]
            insights.append(
                f"Most prolific authors: {', '.join(top_3_authors)}"
            )
        
        # Insight 4: Methods
        unique_methods = len(set(m['name'] for m in entities['methods']))
        if unique_methods > 0:
            insights.append(
                f"Identified {unique_methods} distinct research methods/algorithms"
            )
        
        # Insight 5: Datasets
        unique_datasets = len(set(d['name'] for d in entities['datasets']))
        if unique_datasets > 0:
            insights.append(
                f"Papers utilize {unique_datasets} different datasets"
            )
        
        # Insight 6: Citations
        if citation_analysis:
            avg_citations = (citation_analysis.get('total_citations', 0) / 
                           max(citation_analysis.get('total_papers', 1), 1))
            insights.append(
                f"Average citations per paper: {avg_citations:.1f}"
            )
        
        return insights
    
    def get_capabilities(self) -> List[str]:
        """Get analyzer capabilities"""
        return [
            'analysis',
            'entity_extraction',
            'knowledge_graph_building',
            'citation_analysis',
            'trend_identification',
            'insight_generation'
        ]
    
    def get_analysis_result(self, query: str) -> Optional[Dict]:
        """
        Get cached analysis result
        
        Args:
            query: Research query
            
        Returns:
            Analysis result or None
        """
        return self.analysis_cache.get(query)
    
    def export_knowledge_graph(self, output_path: Path, format: str = 'json'):
        """
        Export knowledge graph
        
        Args:
            output_path: Output file path
            format: Export format ('json' or 'graphml')
        """
        if format == 'json':
            self.kg_builder.export_to_json(output_path)
        elif format == 'graphml':
            self.kg_builder.export_to_graphml(output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        self.logger.info(f"Exported knowledge graph to {output_path}")
