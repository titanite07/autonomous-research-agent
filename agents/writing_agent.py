"""
Writing Agent - Generates research reports, literature reviews, and summaries
"""
from typing import Dict, List, Optional
import logging
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_config import LLMProvider

logger = logging.getLogger(__name__)


class WritingAgent:
    """Agent responsible for generating research documents"""
    
    def __init__(self, provider: str = "ollama", model: Optional[str] = None, temperature: float = 0.7):
        """
        Initialize WritingAgent
        
        Args:
            provider: LLM provider
            model: Model name
            temperature: Temperature for generation (higher = more creative)
        """
        self.llm = LLMProvider.create_llm(provider, model, temperature)
        
        logger.info(f"WritingAgent initialized with {provider}")
    
    def write_literature_review(
        self,
        research_query: str,
        summaries: List[Dict],
        synthesis: Dict,
        citations: List[str],
        format: str = "markdown"
    ) -> str:
        """
        Generate a comprehensive literature review
        
        Args:
            research_query: Original research question
            summaries: List of paper summaries
            synthesis: Synthesis results
            citations: Formatted citations
            format: Output format (markdown, latex, html)
            
        Returns:
            Formatted literature review text
        """
        logger.info(f"Writing literature review for: {research_query}")
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert academic writer specializing in literature reviews.
Write comprehensive, well-structured reviews that synthesize findings from multiple sources.
Use formal academic language and proper citation practices."""),
            ("human", """Write a comprehensive literature review on the following topic:

Research Query: {query}

Number of Papers Reviewed: {num_papers}

Key Themes from Synthesis:
{themes}

Common Findings:
{findings}

Research Gaps:
{gaps}

Please structure the review with:
1. Introduction (context and scope)
2. Thematic Analysis (organized by major themes)
3. Methodological Approaches
4. Key Findings and Debates
5. Research Gaps and Future Directions
6. Conclusion

Use {format} formatting. Include in-text citations where appropriate using [Author, Year] format.""")
        ])
        
        try:
            # Extract synthesis components
            synthesis_text = synthesis.get("synthesis_text", "")
            
            # Prepare findings
            findings_text = "\n".join([
                f"- {s.get('title', '')}: {', '.join(s.get('key_findings', [])[:2])}"
                for s in summaries[:10]
            ])
            
            messages = prompt_template.format_messages(
                query=research_query,
                num_papers=len(summaries),
                themes=synthesis_text[:500],  # Truncate for context
                findings=findings_text,
                gaps="\n".join(synthesis.get("research_gaps", [])[:5]),
                format=format
            )
            
            response = self.llm.invoke(messages)
            review_text = response.content
            
            # Add header and bibliography
            full_review = self._add_header(research_query, len(summaries))
            full_review += "\n\n" + review_text
            full_review += "\n\n## References\n\n"
            full_review += "\n\n".join(citations)
            
            logger.info(f"Literature review generated ({len(full_review)} characters)")
            
            return full_review
            
        except Exception as e:
            logger.error(f"Error writing literature review: {e}")
            return "Error generating literature review"
    
    def write_executive_summary(
        self,
        research_query: str,
        summaries: List[Dict],
        synthesis: Dict,
        max_words: int = 500
    ) -> str:
        """
        Generate an executive summary
        
        Args:
            research_query: Research question
            summaries: Paper summaries
            synthesis: Synthesis results
            max_words: Maximum word count
            
        Returns:
            Executive summary text
        """
        logger.info("Writing executive summary")
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at writing concise executive summaries."),
            ("human", """Write an executive summary (max {max_words} words) for this research:

Research Query: {query}

Papers Analyzed: {num_papers}

Key Synthesis Points:
{synthesis}

Focus on:
- Main findings
- Practical implications
- Key recommendations

Be concise and actionable.""")
        ])
        
        try:
            messages = prompt_template.format_messages(
                query=research_query,
                num_papers=len(summaries),
                synthesis=synthesis.get("synthesis_text", "")[:800],
                max_words=max_words
            )
            
            response = self.llm.invoke(messages)
            
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Error writing executive summary: {e}")
            return "Error generating executive summary"
    
    def write_research_proposal(
        self,
        research_query: str,
        synthesis: Dict,
        format: str = "markdown"
    ) -> str:
        """
        Generate a research proposal based on identified gaps
        
        Args:
            research_query: Research area
            synthesis: Synthesis with identified gaps
            format: Output format
            
        Returns:
            Research proposal text
        """
        logger.info("Writing research proposal")
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at writing research proposals.
Create compelling proposals that clearly articulate research questions, methodology, and significance."""),
            ("human", """Based on the following research synthesis, write a research proposal:

Research Area: {query}

Identified Research Gaps:
{gaps}

Current State of Research:
{synthesis}

Include:
1. Research Question and Objectives
2. Significance and Innovation
3. Proposed Methodology
4. Expected Outcomes
5. Timeline (high-level)

Use {format} formatting.""")
        ])
        
        try:
            gaps = synthesis.get("research_gaps", [])
            gaps_text = "\n".join([f"- {gap}" for gap in gaps])
            
            messages = prompt_template.format_messages(
                query=research_query,
                gaps=gaps_text,
                synthesis=synthesis.get("synthesis_text", "")[:1000],
                format=format
            )
            
            response = self.llm.invoke(messages)
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error writing research proposal: {e}")
            return "Error generating research proposal"
    
    def write_paper_summary(self, paper: Dict, summary: Dict, style: str = "detailed") -> str:
        """
        Write a summary of a single paper
        
        Args:
            paper: Paper metadata
            summary: Paper summary
            style: Summary style (detailed, brief, technical)
            
        Returns:
            Formatted summary
        """
        title = paper.get("title", "Unknown Title")
        authors = ", ".join(paper.get("authors", [])[:3])
        if len(paper.get("authors", [])) > 3:
            authors += " et al."
        
        if style == "brief":
            return f"**{title}** ({authors}): {summary.get('results', '')}"
        
        elif style == "technical":
            output = f"### {title}\n\n"
            output += f"**Authors:** {authors}\n\n"
            output += f"**Methodology:** {summary.get('methodology', 'N/A')}\n\n"
            output += f"**Key Findings:**\n"
            for finding in summary.get("key_findings", []):
                output += f"- {finding}\n"
            output += f"\n**Results:** {summary.get('results', 'N/A')}\n"
            return output
        
        else:  # detailed
            output = f"## {title}\n\n"
            output += f"**Authors:** {authors}\n"
            output += f"**Published:** {paper.get('published_date', 'N/A')}\n"
            output += f"**Source:** {paper.get('source', 'N/A')}\n"
            output += f"**URL:** {paper.get('url', 'N/A')}\n\n"
            output += f"### Abstract\n{paper.get('abstract', 'N/A')}\n\n"
            output += f"### Key Findings\n"
            for finding in summary.get("key_findings", []):
                output += f"- {finding}\n"
            output += f"\n### Methodology\n{summary.get('methodology', 'N/A')}\n\n"
            output += f"### Results\n{summary.get('results', 'N/A')}\n\n"
            
            if summary.get("limitations"):
                output += f"### Limitations\n"
                for limitation in summary.get("limitations", []):
                    output += f"- {limitation}\n"
                output += "\n"
            
            output += f"### Future Work\n{summary.get('future_work', 'N/A')}\n\n"
            output += f"**Relevance Score:** {summary.get('relevance_score', 0)}/10\n"
            
            return output
    
    def write_thematic_analysis(
        self,
        themes: List[str],
        summaries: List[Dict],
        clusters: Dict
    ) -> str:
        """
        Write a thematic analysis section
        
        Args:
            themes: List of identified themes
            summaries: Paper summaries
            clusters: Paper clusters
            
        Returns:
            Thematic analysis text
        """
        logger.info("Writing thematic analysis")
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at thematic analysis in academic research."),
            ("human", """Perform a thematic analysis based on these themes and papers:

Themes Identified:
{themes}

Paper Clusters:
{clusters}

Write a comprehensive thematic analysis that:
1. Discusses each theme in detail
2. Provides examples from the papers
3. Shows how themes interconnect
4. Identifies dominant and emerging themes

Use academic writing style with proper structure.""")
        ])
        
        try:
            themes_text = "\n".join([f"- {theme}" for theme in themes[:7]])
            
            # Summarize clusters
            cluster_text = ""
            for cluster_id, papers in list(clusters.items())[:5]:
                cluster_text += f"\n{cluster_id}: {len(papers)} papers\n"
                for paper in papers[:3]:
                    cluster_text += f"  - {paper.get('title', '')}\n"
            
            messages = prompt_template.format_messages(
                themes=themes_text,
                clusters=cluster_text
            )
            
            response = self.llm.invoke(messages)
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error writing thematic analysis: {e}")
            return "Error generating thematic analysis"
    
    def _add_header(self, title: str, num_papers: int) -> str:
        """Add header to document"""
        return f"""# Literature Review: {title}

**Date:** {datetime.now().strftime("%B %d, %Y")}
**Papers Analyzed:** {num_papers}
**Generated by:** Autonomous Research Agent

---
"""
    
    def export_to_latex(self, markdown_text: str) -> str:
        """
        Convert markdown to LaTeX
        
        Args:
            markdown_text: Markdown formatted text
            
        Returns:
            LaTeX formatted text
        """
        # Basic markdown to LaTeX conversion
        latex = "\\documentclass{article}\n"
        latex += "\\usepackage[utf8]{inputenc}\n"
        latex += "\\usepackage{hyperref}\n\n"
        latex += "\\begin{document}\n\n"
        
        # Convert headers
        text = markdown_text.replace("# ", "\\section{").replace("\n", "}\n", 1)
        text = text.replace("## ", "\\subsection{").replace("\n", "}\n")
        text = text.replace("### ", "\\subsubsection{").replace("\n", "}\n")
        
        # Convert bold
        import re
        text = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', text)
        
        # Convert italic
        text = re.sub(r'\*(.+?)\*', r'\\textit{\1}', text)
        
        # Convert bullet points
        text = re.sub(r'^- (.+)$', r'\\item \1', text, flags=re.MULTILINE)
        
        latex += text
        latex += "\n\n\\end{document}"
        
        return latex
    
    def export_to_html(self, markdown_text: str) -> str:
        """
        Convert markdown to HTML
        
        Args:
            markdown_text: Markdown formatted text
            
        Returns:
            HTML formatted text
        """
        # Simple markdown to HTML conversion
        import re
        
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Literature Review</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; }
        h2 { color: #555; margin-top: 30px; }
        h3 { color: #777; }
        a { color: #0066cc; }
    </style>
</head>
<body>
"""
        
        # Convert markdown to HTML
        text = markdown_text
        text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        text = text.replace('\n\n', '</p><p>')
        
        html += f"<p>{text}</p>"
        html += "\n</body>\n</html>"
        
        return html
    
    def generate_report_package(
        self,
        research_query: str,
        summaries: List[Dict],
        synthesis: Dict,
        citations: List[str],
        output_dir: str = "output"
    ) -> Dict[str, str]:
        """
        Generate a complete report package with multiple formats
        
        Args:
            research_query: Research question
            summaries: Paper summaries
            synthesis: Synthesis results
            citations: Citations
            output_dir: Output directory
            
        Returns:
            Dictionary mapping filenames to content
        """
        logger.info("Generating complete report package")
        
        package = {}
        
        # Literature review
        lit_review = self.write_literature_review(
            research_query, summaries, synthesis, citations
        )
        package["literature_review.md"] = lit_review
        package["literature_review.html"] = self.export_to_html(lit_review)
        package["literature_review.tex"] = self.export_to_latex(lit_review)
        
        # Executive summary
        exec_summary = self.write_executive_summary(research_query, summaries, synthesis)
        package["executive_summary.md"] = exec_summary
        
        # Research proposal
        proposal = self.write_research_proposal(research_query, synthesis)
        package["research_proposal.md"] = proposal
        
        # Individual paper summaries
        all_summaries = ""
        for paper, summary in zip(summaries, summaries):
            all_summaries += self.write_paper_summary(paper, summary) + "\n\n---\n\n"
        package["detailed_summaries.md"] = all_summaries
        
        logger.info(f"Generated {len(package)} documents")
        
        return package
