"""
Report Writer Agent
Generates comprehensive research reports
"""
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from .base_agent import BaseAgent, AgentRole, Task


logger = logging.getLogger(__name__)


class ReportWriterAgent(BaseAgent):
    """
    Report Writer Agent: Generates research reports
    
    Responsibilities:
    - Generate comprehensive research reports
    - Summarize findings and insights
    - Create visualizations and charts
    - Format reports in multiple formats (Markdown, PDF, HTML)
    """
    
    def __init__(
        self,
        agent_id: str = "report_writer",
        llm_config: Optional[Dict] = None,
        output_dir: Optional[Path] = None
    ):
        """
        Initialize Report Writer Agent
        
        Args:
            agent_id: Agent identifier
            llm_config: LLM configuration
            output_dir: Directory to store reports
        """
        super().__init__(agent_id, AgentRole.REPORT_WRITER, llm_config)
        
        # Output directory
        self.output_dir = output_dir or Path("reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generated reports
        self.reports: Dict[str, str] = {}
        
        self.logger.info(f"Report Writer Agent initialized (output: {self.output_dir})")
    
    async def process_task(self, task: Task) -> Any:
        """
        Process report writing tasks
        
        Args:
            task: Task to process
            
        Returns:
            Task result
        """
        if task.task_type == "generate_report":
            return await self._generate_report(task)
        elif task.task_type == "summarize_findings":
            return await self._summarize_findings(task)
        else:
            raise ValueError(f"Unknown task type: {task.task_type}")
    
    async def _generate_report(self, task: Task) -> Dict:
        """
        Generate comprehensive research report
        
        Args:
            task: Report generation task
            
        Returns:
            Report information
        """
        query = task.parameters.get('query', '')
        papers = task.parameters.get('papers', [])
        analysis = task.parameters.get('analysis', {})
        
        self.logger.info(f"Generating report for query: {query}")
        
        # Generate report content
        report_content = self._create_report_content(query, papers, analysis)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"research_report_{timestamp}.md"
        report_path = self.output_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # Store in memory
        self.reports[query] = str(report_path)
        self.memory.store_long_term(f"report_{query}", report_content)
        
        result = {
            'query': query,
            'report_path': str(report_path),
            'report_length': len(report_content),
            'sections': ['Executive Summary', 'Key Findings', 'Trending Concepts', 
                        'Top Authors', 'Citation Analysis', 'Insights', 'Conclusion']
        }
        
        self.logger.info(f"Report generated: {report_path}")
        
        return result
    
    def _create_report_content(
        self,
        query: str,
        papers: List[Dict],
        analysis: Dict
    ) -> str:
        """
        Create report content in Markdown format
        
        Args:
            query: Research query
            papers: List of papers
            analysis: Analysis results
            
        Returns:
            Report content as Markdown
        """
        report = []
        
        # Header
        report.append(f"# Research Report: {query}")
        report.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"\n**Query**: {query}")
        report.append(f"\n---\n")
        
        # Executive Summary
        report.append("## Executive Summary\n")
        report.append(f"This report analyzes **{len(papers)} research papers** related to '{query}'.")
        report.append(f"The analysis identifies key trends, prominent researchers, and significant findings in this domain.\n")
        
        # Key Findings
        report.append("## Key Findings\n")
        
        entity_summary = analysis.get('entity_summary', {})
        if entity_summary:
            report.append("### Entity Summary")
            report.append(f"- **Authors**: {entity_summary.get('total_authors', 0)}")
            report.append(f"- **Concepts**: {entity_summary.get('total_concepts', 0)}")
            report.append(f"- **Methods**: {entity_summary.get('total_methods', 0)}")
            report.append(f"- **Datasets**: {entity_summary.get('total_datasets', 0)}\n")
        
        kg_summary = analysis.get('knowledge_graph', {})
        if kg_summary:
            report.append("### Knowledge Graph")
            report.append(f"- **Nodes**: {kg_summary.get('nodes', 0)}")
            report.append(f"- **Edges**: {kg_summary.get('edges', 0)}")
            report.append(f"- **Density**: {kg_summary.get('density', 0):.4f}\n")
        
        # Trending Concepts
        trending = analysis.get('trending_concepts', [])
        if trending:
            report.append("## Trending Concepts\n")
            report.append("The most discussed concepts in the analyzed papers:\n")
            for i, concept in enumerate(trending, 1):
                name = concept.get('name', 'Unknown')
                freq = concept.get('total_frequency', 0)
                report.append(f"{i}. **{name}** (frequency: {freq})")
            report.append("")
        
        # Top Authors
        top_authors = analysis.get('top_authors', [])
        if top_authors:
            report.append("## Top Authors\n")
            report.append("Most prolific authors in this research area:\n")
            for i, author in enumerate(top_authors, 1):
                name = author.get('name', 'Unknown')
                count = author.get('paper_count', 0)
                report.append(f"{i}. **{name}** ({count} papers)")
            report.append("")
        
        # Citation Analysis
        citation_analysis = analysis.get('citation_analysis')
        if citation_analysis:
            report.append("## Citation Analysis\n")
            report.append(f"- **Total Papers**: {citation_analysis.get('total_papers', 0)}")
            report.append(f"- **Total Citations**: {citation_analysis.get('total_citations', 0)}")
            report.append(f"- **Network Density**: {citation_analysis.get('network_density', 0):.4f}\n")
            
            most_cited = citation_analysis.get('most_cited_papers', [])
            if most_cited:
                report.append("### Most Cited Papers\n")
                for i, paper in enumerate(most_cited, 1):
                    paper_id = paper.get('paper_id', 'Unknown')
                    citations = paper.get('citation_count', 0)
                    report.append(f"{i}. {paper_id} ({citations} citations)")
                report.append("")
        
        # Insights
        insights = analysis.get('insights', [])
        if insights:
            report.append("## Insights\n")
            for insight in insights:
                report.append(f"- {insight}")
            report.append("")
        
        # Sample Papers
        if papers:
            report.append("## Sample Papers\n")
            report.append("Representative papers from the analysis:\n")
            for i, paper in enumerate(papers[:5], 1):
                title = paper.get('title', 'Untitled')
                authors = paper.get('authors', [])
                author_str = ', '.join(authors[:3]) if isinstance(authors, list) else str(authors)
                if len(authors) > 3:
                    author_str += " et al."
                year = paper.get('year', paper.get('published_date', 'N/A'))
                
                report.append(f"\n### {i}. {title}")
                report.append(f"**Authors**: {author_str}")
                report.append(f"**Year**: {year}")
                
                abstract = paper.get('abstract', '')
                if abstract:
                    # Truncate abstract
                    abstract_short = abstract[:200] + "..." if len(abstract) > 200 else abstract
                    report.append(f"**Abstract**: {abstract_short}")
        
        # Conclusion
        report.append("\n## Conclusion\n")
        report.append(f"This analysis of {len(papers)} papers on '{query}' reveals ")
        report.append(f"significant research activity with {entity_summary.get('total_concepts', 0)} ")
        report.append(f"key concepts identified. ")
        
        if trending:
            top_concept = trending[0].get('name', 'the topic')
            report.append(f"The dominant focus is on '{top_concept}', ")
            report.append(f"indicating a strong research emphasis in this area.")
        
        report.append("\n\n---")
        report.append("\n*Report generated by Autonomous Research Agent*")
        
        return '\n'.join(report)
    
    async def _summarize_findings(self, task: Task) -> Dict:
        """
        Generate summary of research findings
        
        Args:
            task: Summarization task
            
        Returns:
            Summary
        """
        analysis = task.parameters.get('analysis', {})
        
        summary = {
            'total_papers': analysis.get('total_papers', 0),
            'key_concepts': [c['name'] for c in analysis.get('trending_concepts', [])[:3]],
            'top_authors': [a['name'] for a in analysis.get('top_authors', [])[:3]],
            'insights': analysis.get('insights', [])[:3]
        }
        
        return summary
    
    def get_capabilities(self) -> List[str]:
        """Get report writer capabilities"""
        return [
            'report_writing',
            'report_generation',
            'summarization',
            'markdown_formatting'
        ]
    
    def get_report_path(self, query: str) -> Optional[str]:
        """
        Get report path for a query
        
        Args:
            query: Research query
            
        Returns:
            Report path or None
        """
        return self.reports.get(query)
    
    def list_reports(self) -> List[str]:
        """List all generated reports"""
        return list(self.reports.values())
