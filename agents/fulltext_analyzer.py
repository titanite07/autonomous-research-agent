"""
Full Text Analyzer - Extracts structured information from full paper text
"""
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class FullTextAnalyzer:
    """Analyzes full text of research papers"""
    
    def __init__(self):
        """Initialize Full Text Analyzer"""
        logger.info("FullTextAnalyzer initialized")
    
    def extract_sections(self, full_text: str) -> Dict[str, str]:
        """
        Extract common paper sections
        
        Args:
            full_text: Complete paper text
            
        Returns:
            Dictionary of section name to content
        """
        sections = {}
        
        # Common section headers (case-insensitive)
        section_patterns = [
            (r'\n\s*abstract\s*\n', 'abstract'),
            (r'\n\s*introduction\s*\n', 'introduction'),
            (r'\n\s*related work\s*\n', 'related_work'),
            (r'\n\s*methodology\s*\n', 'methodology'),
            (r'\n\s*method\s*\n', 'methodology'),
            (r'\n\s*experiments?\s*\n', 'experiments'),
            (r'\n\s*results?\s*\n', 'results'),
            (r'\n\s*discussion\s*\n', 'discussion'),
            (r'\n\s*conclusion\s*\n', 'conclusion'),
            (r'\n\s*references?\s*\n', 'references'),
        ]
        
        # Find section boundaries
        found_sections = []
        for pattern, section_name in section_patterns:
            matches = list(re.finditer(pattern, full_text, re.IGNORECASE))
            for match in matches:
                found_sections.append((match.start(), section_name))
        
        # Sort by position
        found_sections.sort()
        
        # Extract content between sections
        for i, (start_pos, section_name) in enumerate(found_sections):
            # Find end position (start of next section or end of text)
            if i + 1 < len(found_sections):
                end_pos = found_sections[i + 1][0]
            else:
                end_pos = len(full_text)
            
            # Extract and clean section text
            section_text = full_text[start_pos:end_pos].strip()
            
            # Remove section header
            section_text = re.sub(r'^.*?\n', '', section_text, count=1)
            
            sections[section_name] = section_text[:5000]  # Limit to 5000 chars per section
        
        logger.info(f"Extracted {len(sections)} sections from full text")
        return sections
    
    def extract_key_sentences(self, text: str, n: int = 5) -> List[str]:
        """
        Extract key sentences from text (simple heuristic)
        
        Args:
            text: Input text
            n: Number of sentences to extract
            
        Returns:
            List of key sentences
        """
        # Split into sentences
        sentences = re.split(r'[.!?]+\s+', text)
        
        # Score sentences by length and keyword presence
        keywords = [
            'propose', 'demonstrate', 'show', 'achieve', 'improve',
            'novel', 'significant', 'performance', 'results', 'method',
            'accuracy', 'outperform', 'state-of-the-art'
        ]
        
        scored_sentences = []
        for sentence in sentences:
            if len(sentence) < 20 or len(sentence) > 300:
                continue
            
            # Simple scoring: length + keyword count
            score = len(sentence.split())
            score += sum(5 for keyword in keywords if keyword in sentence.lower())
            
            scored_sentences.append((score, sentence.strip()))
        
        # Sort by score and take top N
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        key_sentences = [sent for _, sent in scored_sentences[:n]]
        
        return key_sentences
    
    def count_figures_tables(self, full_text: str) -> Dict[str, int]:
        """
        Count figures and tables in paper
        
        Args:
            full_text: Complete paper text
            
        Returns:
            Dictionary with counts
        """
        # Look for figure/table references
        figure_pattern = r'\b(figure|fig\.?)\s+\d+\b'
        table_pattern = r'\btable\s+\d+\b'
        
        figures = len(set(re.findall(figure_pattern, full_text, re.IGNORECASE)))
        tables = len(set(re.findall(table_pattern, full_text, re.IGNORECASE)))
        
        return {
            'figures': figures,
            'tables': tables,
            'total_visual_elements': figures + tables
        }
    
    def count_equations(self, full_text: str) -> int:
        """
        Count equations in paper (simple heuristic)
        
        Args:
            full_text: Complete paper text
            
        Returns:
            Estimated equation count
        """
        # Look for LaTeX equation markers
        equation_patterns = [
            r'\$\$.*?\$\$',  # Display equations
            r'\\begin\{equation\}.*?\\end\{equation\}',
            r'\\begin\{align\}.*?\\end\{align\}',
            r'\\begin\{eqnarray\}.*?\\end\{eqnarray\}'
        ]
        
        count = 0
        for pattern in equation_patterns:
            count += len(re.findall(pattern, full_text, re.DOTALL))
        
        return count
    
    def extract_citations_count(self, full_text: str) -> int:
        """
        Count citations in paper
        
        Args:
            full_text: Complete paper text
            
        Returns:
            Estimated citation count
        """
        # Look for citation patterns [1], [2,3], (Author, Year)
        patterns = [
            r'\[\d+\]',  # [1]
            r'\[\d+,\s*\d+\]',  # [1, 2]
            r'\[\d+-\d+\]',  # [1-5]
            r'\([A-Z][a-z]+,\s*\d{4}\)',  # (Smith, 2020)
        ]
        
        citations = set()
        for pattern in patterns:
            matches = re.findall(pattern, full_text)
            citations.update(matches)
        
        return len(citations)
    
    def analyze_full_paper(self, full_text: str) -> Dict:
        """
        Comprehensive analysis of full paper
        
        Args:
            full_text: Complete paper text
            
        Returns:
            Dictionary with analysis results
        """
        logger.info("Analyzing full paper text")
        
        # Extract sections
        sections = self.extract_sections(full_text)
        
        # Count elements
        visual_counts = self.count_figures_tables(full_text)
        equation_count = self.count_equations(full_text)
        citation_count = self.extract_citations_count(full_text)
        
        # Extract key insights from methodology and results
        methodology_text = sections.get('methodology', sections.get('method', ''))
        results_text = sections.get('results', sections.get('experiments', ''))
        
        key_methodology_sentences = self.extract_key_sentences(methodology_text, n=3)
        key_results_sentences = self.extract_key_sentences(results_text, n=3)
        
        # Word count
        word_count = len(full_text.split())
        
        analysis = {
            'word_count': word_count,
            'sections_found': list(sections.keys()),
            'has_abstract': 'abstract' in sections,
            'has_introduction': 'introduction' in sections,
            'has_methodology': 'methodology' in sections or 'method' in sections,
            'has_results': 'results' in sections or 'experiments' in sections,
            'has_conclusion': 'conclusion' in sections,
            'figures_count': visual_counts['figures'],
            'tables_count': visual_counts['tables'],
            'equations_count': equation_count,
            'citations_count': citation_count,
            'key_methodology': key_methodology_sentences,
            'key_results': key_results_sentences,
            'sections': sections  # Full section texts
        }
        
        logger.info(f"Analysis complete: {len(sections)} sections, {word_count} words")
        return analysis
    
    def create_enhanced_abstract(self, full_text: str, original_abstract: str) -> str:
        """
        Create enhanced abstract with key findings from full text
        
        Args:
            full_text: Complete paper text
            original_abstract: Original abstract
            
        Returns:
            Enhanced abstract
        """
        analysis = self.analyze_full_paper(full_text)
        
        # Build enhanced abstract
        enhanced_parts = [
            f"Original Abstract: {original_abstract}",
            "",
            "Key Methodology:",
        ]
        
        for sentence in analysis.get('key_methodology', [])[:2]:
            enhanced_parts.append(f"- {sentence}")
        
        enhanced_parts.append("")
        enhanced_parts.append("Key Results:")
        
        for sentence in analysis.get('key_results', [])[:2]:
            enhanced_parts.append(f"- {sentence}")
        
        enhanced_parts.append("")
        enhanced_parts.append(f"Paper Statistics:")
        enhanced_parts.append(f"- Word Count: {analysis.get('word_count', 0):,}")
        enhanced_parts.append(f"- Figures: {analysis.get('figures_count', 0)}")
        enhanced_parts.append(f"- Tables: {analysis.get('tables_count', 0)}")
        enhanced_parts.append(f"- Equations: {analysis.get('equations_count', 0)}")
        
        return "\n".join(enhanced_parts)
