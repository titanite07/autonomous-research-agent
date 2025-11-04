"""
Extract citations from research papers
"""
import re
import logging
from typing import List, Dict, Optional, Set
from pathlib import Path

logger = logging.getLogger(__name__)


class CitationExtractor:
    """Extract citations from research papers"""
    
    # Common citation patterns
    CITATION_PATTERNS = [
        # Author et al. (Year)
        r'([A-Z][a-z]+(?:\s+et\s+al\.)?)\s*\((\d{4}[a-z]?)\)',
        # [Number] style
        r'\[(\d+)\]',
        # [Author, Year]
        r'\[([A-Z][a-z]+(?:\s+et\s+al\.)?,\s*\d{4}[a-z]?)\]',
    ]
    
    # arXiv ID pattern
    ARXIV_PATTERN = r'arXiv:(\d{4}\.\d{4,5}(?:v\d+)?)'
    
    # DOI pattern
    DOI_PATTERN = r'10\.\d{4,}/[^\s]+'
    
    def __init__(self):
        """Initialize citation extractor"""
        self.compiled_patterns = [re.compile(p) for p in self.CITATION_PATTERNS]
        self.arxiv_re = re.compile(self.ARXIV_PATTERN)
        self.doi_re = re.compile(self.DOI_PATTERN)
    
    def extract_from_text(self, text: str) -> List[Dict[str, str]]:
        """
        Extract citations from text
        
        Args:
            text: Text to extract citations from
            
        Returns:
            List of citation dictionaries
        """
        citations = []
        seen = set()
        
        # Extract author-year citations
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                citation_str = match.group(0)
                if citation_str not in seen:
                    citations.append({
                        'type': 'inline',
                        'raw': citation_str,
                        'text': match.group(1) if match.lastindex >= 1 else citation_str
                    })
                    seen.add(citation_str)
        
        # Extract arXiv IDs
        for match in self.arxiv_re.finditer(text):
            arxiv_id = match.group(1)
            if arxiv_id not in seen:
                citations.append({
                    'type': 'arxiv',
                    'raw': match.group(0),
                    'arxiv_id': arxiv_id
                })
                seen.add(arxiv_id)
        
        # Extract DOIs
        for match in self.doi_re.finditer(text):
            doi = match.group(0)
            if doi not in seen:
                citations.append({
                    'type': 'doi',
                    'raw': match.group(0),
                    'doi': doi
                })
                seen.add(doi)
        
        return citations
    
    def extract_from_references(self, references_text: str) -> List[Dict[str, any]]:
        """
        Extract structured citations from references section
        
        Args:
            references_text: References section text
            
        Returns:
            List of structured citation dictionaries
        """
        citations = []
        
        # Split by lines (each reference usually on separate line or numbered)
        lines = references_text.split('\n')
        current_ref = []
        ref_number = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_ref:
                    # Process accumulated reference
                    ref_text = ' '.join(current_ref)
                    citation = self._parse_reference(ref_text, ref_number)
                    if citation:
                        citations.append(citation)
                    current_ref = []
                    ref_number += 1
                continue
            
            # Check if line starts with number (new reference)
            if re.match(r'^\[?\d+[\].]', line):
                if current_ref:
                    ref_text = ' '.join(current_ref)
                    citation = self._parse_reference(ref_text, ref_number)
                    if citation:
                        citations.append(citation)
                    current_ref = []
                ref_number += 1
            
            current_ref.append(line)
        
        # Process last reference
        if current_ref:
            ref_text = ' '.join(current_ref)
            citation = self._parse_reference(ref_text, ref_number)
            if citation:
                citations.append(citation)
        
        return citations
    
    def _parse_reference(self, ref_text: str, ref_number: int) -> Optional[Dict[str, any]]:
        """
        Parse a single reference into structured data
        
        Args:
            ref_text: Reference text
            ref_number: Reference number
            
        Returns:
            Parsed citation dictionary or None
        """
        if not ref_text or len(ref_text) < 10:
            return None
        
        citation = {
            'ref_number': ref_number,
            'raw': ref_text,
            'authors': None,
            'title': None,
            'year': None,
            'venue': None,
            'arxiv_id': None,
            'doi': None
        }
        
        # Extract year
        year_match = re.search(r'\b(19|20)\d{2}\b', ref_text)
        if year_match:
            citation['year'] = int(year_match.group(0))
        
        # Extract arXiv ID
        arxiv_match = self.arxiv_re.search(ref_text)
        if arxiv_match:
            citation['arxiv_id'] = arxiv_match.group(1)
        
        # Extract DOI
        doi_match = self.doi_re.search(ref_text)
        if doi_match:
            citation['doi'] = doi_match.group(0)
        
        # Extract authors (before year typically)
        if year_match:
            before_year = ref_text[:year_match.start()].strip()
            # Remove leading numbers/brackets
            before_year = re.sub(r'^\[?\d+[\].]\s*', '', before_year)
            # Authors are typically at the start, separated by commas or 'and'
            if before_year:
                citation['authors'] = before_year.strip('.,; ')
        
        # Extract title (often in quotes or between authors and venue)
        title_match = re.search(r'["""]([^"""]+)["""]', ref_text)
        if title_match:
            citation['title'] = title_match.group(1)
        elif year_match:
            # Try to get text after year as potential venue/title
            after_year = ref_text[year_match.end():].strip()
            # First sentence-like text could be title
            parts = re.split(r'[.]\s+', after_year, 1)
            if parts and len(parts[0]) > 20:
                citation['title'] = parts[0].strip('.,; ')
        
        return citation
    
    def extract_from_pdf_data(self, pdf_data: Dict) -> Dict[str, List]:
        """
        Extract citations from PDF extraction data
        
        Args:
            pdf_data: PDF data from EnhancedPDFManager
            
        Returns:
            Dictionary with inline citations and references
        """
        result = {
            'inline_citations': [],
            'references': []
        }
        
        # Extract from sections
        sections = pdf_data.get('sections', {})
        for section_name, section_data in sections.items():
            content = section_data.get('content', '')
            if content:
                inline = self.extract_from_text(content)
                result['inline_citations'].extend(inline)
        
        # Extract from references section
        if 'references' in sections or 'REFERENCES' in sections:
            ref_section = sections.get('references') or sections.get('REFERENCES')
            ref_content = ref_section.get('content', '')
            if ref_content:
                refs = self.extract_from_references(ref_content)
                result['references'].extend(refs)
        
        # Remove duplicates
        result['inline_citations'] = self._deduplicate_citations(result['inline_citations'])
        result['references'] = self._deduplicate_references(result['references'])
        
        return result
    
    def _deduplicate_citations(self, citations: List[Dict]) -> List[Dict]:
        """Remove duplicate citations"""
        seen = set()
        unique = []
        
        for citation in citations:
            key = citation.get('raw', '')
            if key and key not in seen:
                seen.add(key)
                unique.append(citation)
        
        return unique
    
    def _deduplicate_references(self, references: List[Dict]) -> List[Dict]:
        """Remove duplicate references"""
        seen = set()
        unique = []
        
        for ref in references:
            # Use multiple fields for deduplication
            key = (
                ref.get('arxiv_id'),
                ref.get('doi'),
                ref.get('title'),
                ref.get('authors')
            )
            if key not in seen:
                seen.add(key)
                unique.append(ref)
        
        return unique
    
    def match_citations_to_references(self, 
                                     inline_citations: List[Dict],
                                     references: List[Dict]) -> Dict[str, Dict]:
        """
        Match inline citations to reference list
        
        Args:
            inline_citations: List of inline citations
            references: List of references
            
        Returns:
            Dictionary mapping citation text to reference
        """
        matches = {}
        
        for citation in inline_citations:
            citation_text = citation.get('text', '')
            citation_raw = citation.get('raw', '')
            
            # Try to find matching reference
            best_match = None
            
            for ref in references:
                # Match by number
                if citation.get('type') == 'inline' and citation_text.isdigit():
                    if ref.get('ref_number') == int(citation_text):
                        best_match = ref
                        break
                
                # Match by author-year
                if ref.get('authors') and ref.get('year'):
                    authors = ref['authors'].lower()
                    year = str(ref['year'])
                    citation_lower = citation_text.lower()
                    
                    if year in citation_raw and any(
                        author_part in citation_lower 
                        for author_part in authors.split()[:2]
                    ):
                        best_match = ref
                        break
            
            if best_match:
                matches[citation_raw] = best_match
        
        return matches
