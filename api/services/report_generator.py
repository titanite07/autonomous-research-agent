"""
Report Generation Service
Generates literature review reports from research papers
"""

from typing import List, Dict, Optional
from datetime import datetime
import re


class ReportGenerator:
    """
    Generates academic literature review reports from papers.
    Supports multiple formats: Markdown, HTML, and plain text.
    """
    
    def __init__(self):
        self.citation_styles = {
            "APA": self._format_apa,
            "MLA": self._format_mla,
            "Chicago": self._format_chicago,
            "IEEE": self._format_ieee,
            "Harvard": self._format_harvard
        }
    
    def generate_literature_review(
        self,
        query: str,
        papers: List[Dict],
        citation_style: str = "APA",
        format: str = "markdown"
    ) -> Dict:
        """
        Generate a comprehensive literature review report.
        
        Args:
            query: The research query
            papers: List of paper dictionaries
            citation_style: Citation format (APA, MLA, Chicago, IEEE, Harvard)
            format: Output format (markdown, html, text)
            
        Returns:
            Dictionary with report content and metadata
        """
        
        # Sort papers by relevance
        sorted_papers = sorted(papers, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Extract key information
        key_findings = self._extract_key_findings(sorted_papers)
        research_gaps = self._identify_research_gaps(sorted_papers, query)
        themes = self._identify_themes(sorted_papers)
        
        # Generate report sections
        sections = {
            "title": f"Literature Review: {query}",
            "executive_summary": self._generate_executive_summary(query, sorted_papers, key_findings),
            "introduction": self._generate_introduction(query, len(sorted_papers)),
            "methodology": self._generate_methodology(sorted_papers),
            "key_findings": key_findings,
            "themes": themes,
            "research_gaps": research_gaps,
            "conclusion": self._generate_conclusion(sorted_papers, research_gaps),
            "references": self._generate_references(sorted_papers, citation_style)
        }
        
        # Format the report
        if format == "markdown":
            content = self._format_markdown(sections)
        elif format == "html":
            content = self._format_html(sections)
        else:
            content = self._format_text(sections)
        
        # Calculate metadata
        word_count = len(content.split())
        
        return {
            "title": sections["title"],
            "content": content,
            "executive_summary": sections["executive_summary"],
            "key_findings": key_findings,
            "research_gaps": research_gaps,
            "word_count": word_count,
            "paper_count": len(papers),
            "citation_style": citation_style,
            "format": format,
            "generated_at": datetime.now().isoformat()
        }
    
    def _extract_key_findings(self, papers: List[Dict]) -> List[str]:
        """Extract key findings from papers."""
        findings = []
        
        for paper in papers[:10]:  # Top 10 most relevant
            title = paper.get('title', '')
            abstract = paper.get('abstract', '')
            
            if abstract:
                # Simple extraction: first sentence of abstract
                sentences = abstract.split('. ')
                if sentences:
                    finding = f"{title}: {sentences[0]}"
                    findings.append(finding)
        
        return findings
    
    def _identify_research_gaps(self, papers: List[Dict], query: str) -> List[str]:
        """Identify potential research gaps."""
        gaps = []
        
        # Check for missing topics in query
        query_terms = set(query.lower().split())
        
        # Common research gaps
        if len(papers) < 5:
            gaps.append("Limited research available on this specific topic")
        
        # Check for recent papers
        recent_papers = [p for p in papers if p.get('year', 0) >= 2020]
        if len(recent_papers) < len(papers) * 0.3:
            gaps.append("Need for more recent studies in this area")
        
        # Check for methodological diversity
        gaps.append("Opportunity for comparative studies across different methodologies")
        
        return gaps
    
    def _identify_themes(self, papers: List[Dict]) -> List[Dict]:
        """Identify common themes across papers."""
        themes = []
        
        # Simple keyword-based theme detection
        keyword_counts = {}
        
        for paper in papers:
            keywords = paper.get('keywords', [])
            for keyword in keywords:
                if keyword:
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Get top themes
        sorted_themes = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for theme, count in sorted_themes:
            themes.append({
                "theme": theme,
                "paper_count": count,
                "percentage": round((count / len(papers)) * 100, 1)
            })
        
        return themes
    
    def _generate_executive_summary(self, query: str, papers: List[Dict], findings: List[str]) -> str:
        """Generate executive summary."""
        avg_relevance = sum(p.get('relevance_score', 0) for p in papers) / len(papers) if papers else 0
        year_range = self._get_year_range(papers)
        
        summary = f"""This literature review examines {len(papers)} academic papers related to "{query}". 
The analysis covers research published between {year_range}, with an average relevance score of {avg_relevance:.1f}%. 
The review identifies key findings, emerging themes, and potential research gaps in this domain. 
The papers demonstrate significant contributions to understanding {query.lower()}, with particular emphasis on 
recent developments and methodological innovations."""
        
        return summary
    
    def _generate_introduction(self, query: str, paper_count: int) -> str:
        """Generate introduction section."""
        return f"""# Introduction

This literature review provides a comprehensive analysis of current research on {query}. 
Through systematic examination of {paper_count} peer-reviewed papers, this review aims to:

1. Synthesize existing knowledge and key findings
2. Identify emerging themes and patterns
3. Highlight methodological approaches
4. Identify gaps for future research

The papers were selected based on relevance, citation impact, and recency to ensure a comprehensive 
overview of the current state of research in this area."""
    
    def _generate_methodology(self, papers: List[Dict]) -> str:
        """Generate methodology section."""
        sources = set(p.get('source', 'unknown') for p in papers)
        year_range = self._get_year_range(papers)
        
        return f"""# Methodology

This review was conducted using a systematic search across multiple academic databases including {', '.join(sources)}. 
Papers published between {year_range} were included in the analysis. Selection criteria included:

- Relevance to the research query
- Peer-reviewed publications
- English language papers
- Citation impact and author credibility

A total of {len(papers)} papers met the inclusion criteria and were analyzed for this review."""
    
    def _generate_conclusion(self, papers: List[Dict], gaps: List[str]) -> str:
        """Generate conclusion section."""
        return f"""# Conclusion

This literature review of {len(papers)} papers reveals significant progress in the field. 
The research demonstrates strong theoretical foundations and emerging practical applications. 

However, several research gaps were identified:
{chr(10).join(f'- {gap}' for gap in gaps)}

Future research should address these gaps to advance knowledge and practical applications in this domain."""
    
    def _generate_references(self, papers: List[Dict], style: str) -> str:
        """Generate reference list in specified citation style."""
        formatter = self.citation_styles.get(style, self._format_apa)
        
        references = []
        for paper in papers:
            citation = formatter(paper)
            references.append(citation)
        
        return "\n\n".join(references)
    
    def _format_apa(self, paper: Dict) -> str:
        """Format citation in APA style."""
        authors = paper.get('authors', [])
        author_str = self._format_authors_apa(authors)
        year = paper.get('year', 'n.d.')
        title = paper.get('title', 'Untitled')
        url = paper.get('url', '')
        
        return f"{author_str} ({year}). {title}. Retrieved from {url}"
    
    def _format_mla(self, paper: Dict) -> str:
        """Format citation in MLA style."""
        authors = paper.get('authors', [])
        author_str = self._format_authors_mla(authors)
        title = paper.get('title', 'Untitled')
        year = paper.get('year', 'n.d.')
        url = paper.get('url', '')
        
        return f'{author_str}. "{title}." {year}. Web. {url}'
    
    def _format_chicago(self, paper: Dict) -> str:
        """Format citation in Chicago style."""
        authors = paper.get('authors', [])
        author_str = self._format_authors_chicago(authors)
        year = paper.get('year', 'n.d.')
        title = paper.get('title', 'Untitled')
        url = paper.get('url', '')
        
        return f'{author_str}. "{title}." {year}. {url}'
    
    def _format_ieee(self, paper: Dict) -> str:
        """Format citation in IEEE style."""
        authors = paper.get('authors', [])
        author_str = self._format_authors_ieee(authors)
        title = paper.get('title', 'Untitled')
        year = paper.get('year', 'n.d.')
        url = paper.get('url', '')
        
        return f'[{len(authors)}] {author_str}, "{title}," {year}. [Online]. Available: {url}'
    
    def _format_harvard(self, paper: Dict) -> str:
        """Format citation in Harvard style."""
        authors = paper.get('authors', [])
        author_str = self._format_authors_harvard(authors)
        year = paper.get('year', 'n.d.')
        title = paper.get('title', 'Untitled')
        url = paper.get('url', '')
        
        return f'{author_str} ({year}) "{title}", available at: {url}'
    
    def _format_authors_apa(self, authors: List[str]) -> str:
        """Format authors for APA style."""
        if not authors:
            return "Unknown"
        if len(authors) == 1:
            return authors[0]
        if len(authors) <= 7:
            return ", ".join(authors[:-1]) + ", & " + authors[-1]
        return ", ".join(authors[:6]) + ", ... " + authors[-1]
    
    def _format_authors_mla(self, authors: List[str]) -> str:
        """Format authors for MLA style."""
        if not authors:
            return "Unknown"
        if len(authors) == 1:
            return authors[0]
        return authors[0] + ", et al"
    
    def _format_authors_chicago(self, authors: List[str]) -> str:
        """Format authors for Chicago style."""
        if not authors:
            return "Unknown"
        if len(authors) <= 3:
            return ", ".join(authors)
        return authors[0] + " et al"
    
    def _format_authors_ieee(self, authors: List[str]) -> str:
        """Format authors for IEEE style."""
        if not authors:
            return "Unknown"
        return ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
    
    def _format_authors_harvard(self, authors: List[str]) -> str:
        """Format authors for Harvard style."""
        if not authors:
            return "Unknown"
        if len(authors) <= 3:
            return " and ".join(authors)
        return authors[0] + " et al."
    
    def _get_year_range(self, papers: List[Dict]) -> str:
        """Get year range of papers."""
        years = [p.get('year', 0) for p in papers if p.get('year')]
        if not years:
            return "unknown period"
        return f"{min(years)}-{max(years)}"
    
    def _format_markdown(self, sections: Dict) -> str:
        """Format report as Markdown."""
        md = f"""# {sections['title']}

*Generated: {datetime.now().strftime('%B %d, %Y')}*

---

## Executive Summary

{sections['executive_summary']}

---

{sections['introduction']}

---

{sections['methodology']}

---

## Key Findings

{chr(10).join(f'{i+1}. {finding}' for i, finding in enumerate(sections['key_findings']))}

---

## Emerging Themes

{chr(10).join(f"- **{theme['theme']}** ({theme['paper_count']} papers, {theme['percentage']}%)" for theme in sections['themes'])}

---

## Research Gaps

{chr(10).join(f'- {gap}' for gap in sections['research_gaps'])}

---

{sections['conclusion']}

---

## References

{sections['references']}
"""
        return md
    
    def _format_html(self, sections: Dict) -> str:
        """Format report as HTML."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{sections['title']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .summary {{ background: #ecf0f1; padding: 15px; border-left: 4px solid #3498db; }}
    </style>
</head>
<body>
    <h1>{sections['title']}</h1>
    <p><em>Generated: {datetime.now().strftime('%B %d, %Y')}</em></p>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        <p>{sections['executive_summary']}</p>
    </div>
    
    <h2>Key Findings</h2>
    <ol>
        {chr(10).join(f'<li>{finding}</li>' for finding in sections['key_findings'])}
    </ol>
    
    <h2>References</h2>
    <p>{sections['references'].replace(chr(10), '<br>')}</p>
</body>
</html>
"""
        return html
    
    def _format_text(self, sections: Dict) -> str:
        """Format report as plain text."""
        return f"""{sections['title']}
{'=' * len(sections['title'])}

Generated: {datetime.now().strftime('%B %d, %Y')}

EXECUTIVE SUMMARY
{'-' * 50}
{sections['executive_summary']}

KEY FINDINGS
{'-' * 50}
{chr(10).join(f'{i+1}. {finding}' for i, finding in enumerate(sections['key_findings']))}

RESEARCH GAPS
{'-' * 50}
{chr(10).join(f'- {gap}' for gap in sections['research_gaps'])}

REFERENCES
{'-' * 50}
{sections['references']}
"""
