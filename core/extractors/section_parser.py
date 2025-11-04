"""
Section Parser - Parse structured sections from research papers
"""
from pathlib import Path
from typing import List, Dict, Optional
import logging
import re

logger = logging.getLogger(__name__)


class SectionParser:
    """Parse structured sections from research papers"""
    
    # Common section headers in research papers
    COMMON_SECTIONS = {
        'abstract': ['abstract', 'summary'],
        'introduction': ['introduction', 'background'],
        'related_work': ['related work', 'literature review', 'previous work', 'prior art'],
        'methodology': ['methodology', 'methods', 'approach', 'materials and methods'],
        'experiments': ['experiments', 'experimental setup', 'experimental results'],
        'results': ['results', 'findings', 'evaluation'],
        'discussion': ['discussion', 'analysis'],
        'conclusion': ['conclusion', 'conclusions', 'summary', 'future work'],
        'references': ['references', 'bibliography', 'citations'],
        'acknowledgments': ['acknowledgments', 'acknowledgements']
    }
    
    def __init__(self):
        """Initialize section parser"""
        logger.info("SectionParser initialized")
    
    def parse_sections(self, pdf_path: Path) -> Dict[str, str]:
        """
        Parse sections from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary mapping section names to their content
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.error("PyMuPDF not installed. Install with: pip install pymupdf")
            return {}
        
        try:
            logger.info(f"Parsing sections from {pdf_path}")
            
            doc = fitz.open(str(pdf_path))
            
            # Extract full text with page markers
            full_text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                full_text += f"\n\n--- PAGE {page_num + 1} ---\n\n{text}"
            
            doc.close()
            
            # Parse sections
            sections = self._parse_text_into_sections(full_text)
            
            logger.info(f"Found {len(sections)} sections")
            return sections
        
        except Exception as e:
            logger.error(f"Error parsing sections: {e}")
            return {}
    
    def _parse_text_into_sections(self, text: str) -> Dict[str, str]:
        """Parse text into sections based on headers"""
        sections = {}
        
        # Find all section boundaries
        boundaries = self._find_section_boundaries(text)
        
        if not boundaries:
            logger.warning("No section boundaries found, treating as single document")
            return {'full_text': text}
        
        # Extract content between boundaries
        for i, (section_name, start_pos) in enumerate(boundaries):
            # Get end position (start of next section or end of text)
            end_pos = boundaries[i + 1][1] if i + 1 < len(boundaries) else len(text)
            
            # Extract content
            content = text[start_pos:end_pos].strip()
            
            # Remove the section header from content
            lines = content.split('\n')
            if lines:
                lines = lines[1:]  # Skip header line
            content = '\n'.join(lines).strip()
            
            sections[section_name] = content
        
        return sections
    
    def _find_section_boundaries(self, text: str) -> List[tuple]:
        """Find section boundaries in text"""
        boundaries = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_clean = line.strip().lower()
            
            if not line_clean:
                continue
            
            # Check if line matches any section header
            section_name = self._identify_section(line_clean)
            
            if section_name:
                # Get position in original text
                pos = text.find(line)
                boundaries.append((section_name, pos))
                logger.debug(f"Found section '{section_name}' at line {i}")
        
        # Sort by position
        boundaries.sort(key=lambda x: x[1])
        
        return boundaries
    
    def _identify_section(self, line: str) -> Optional[str]:
        """Identify if line is a section header"""
        # Remove numbers and special characters
        line_clean = re.sub(r'^\d+\.?\s*', '', line)
        line_clean = re.sub(r'[^\w\s]', '', line_clean).strip()
        
        # Check against known sections
        for section_type, keywords in self.COMMON_SECTIONS.items():
            for keyword in keywords:
                if line_clean == keyword or line_clean.startswith(keyword):
                    return section_type
        
        # Check for numbered sections (e.g., "1. Introduction")
        if re.match(r'^\d+\.?\s+[a-z\s]+$', line):
            return 'numbered_section'
        
        return None
    
    def extract_abstract(self, pdf_path: Path) -> str:
        """
        Extract only the abstract section
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Abstract text or empty string if not found
        """
        sections = self.parse_sections(pdf_path)
        return sections.get('abstract', '')
    
    def extract_main_content(self, pdf_path: Path) -> str:
        """
        Extract main content (excluding abstract, references, acknowledgments)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Main content text
        """
        sections = self.parse_sections(pdf_path)
        
        # Exclude non-content sections
        exclude = ['abstract', 'references', 'acknowledgments']
        
        main_content = []
        for section_name, content in sections.items():
            if section_name not in exclude:
                main_content.append(f"## {section_name.upper()}\n\n{content}")
        
        return '\n\n'.join(main_content)
    
    def get_section_statistics(self, sections: Dict[str, str]) -> Dict:
        """
        Get statistics about sections
        
        Args:
            sections: Dictionary of section content
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'total_sections': len(sections),
            'total_words': sum(len(content.split()) for content in sections.values()),
            'total_characters': sum(len(content) for content in sections.values()),
            'sections_found': list(sections.keys()),
            'section_word_counts': {name: len(content.split()) 
                                   for name, content in sections.items()},
            'longest_section': max(sections.items(), key=lambda x: len(x[1]))[0] if sections else None,
            'shortest_section': min(sections.items(), key=lambda x: len(x[1]))[0] if sections else None
        }
        
        return stats
    
    def analyze_structure(self, sections: Dict[str, str]) -> Dict:
        """
        Analyze document structure
        
        Args:
            sections: Dictionary of section content
            
        Returns:
            Structure analysis
        """
        analysis = {
            'has_abstract': 'abstract' in sections,
            'has_introduction': 'introduction' in sections,
            'has_methodology': 'methodology' in sections,
            'has_results': 'results' in sections or 'experiments' in sections,
            'has_conclusion': 'conclusion' in sections,
            'has_references': 'references' in sections,
            'section_order': list(sections.keys()),
            'is_well_structured': self._check_well_structured(sections)
        }
        
        return analysis
    
    def _check_well_structured(self, sections: Dict[str, str]) -> bool:
        """Check if document follows typical research paper structure"""
        required_sections = ['abstract', 'introduction', 'conclusion']
        return all(section in sections for section in required_sections)
    
    def extract_subsections(self, section_text: str) -> Dict[str, str]:
        """
        Extract subsections from a section
        
        Args:
            section_text: Text of a section
            
        Returns:
            Dictionary of subsection content
        """
        subsections = {}
        
        # Pattern for subsection headers (e.g., "3.1 Dataset", "3.1.1 Preprocessing")
        pattern = r'^(\d+\.)+\d+\s+([A-Z][^\n]+)$'
        
        lines = section_text.split('\n')
        current_subsection = None
        current_content = []
        
        for line in lines:
            match = re.match(pattern, line.strip())
            
            if match:
                # Save previous subsection
                if current_subsection:
                    subsections[current_subsection] = '\n'.join(current_content).strip()
                
                # Start new subsection
                current_subsection = match.group(2).strip()
                current_content = []
            else:
                if current_subsection:
                    current_content.append(line)
        
        # Save last subsection
        if current_subsection:
            subsections[current_subsection] = '\n'.join(current_content).strip()
        
        return subsections
    
    def format_as_markdown(self, sections: Dict[str, str]) -> str:
        """
        Format sections as Markdown
        
        Args:
            sections: Dictionary of section content
            
        Returns:
            Markdown formatted text
        """
        markdown = []
        
        for section_name, content in sections.items():
            # Format section header
            header = section_name.replace('_', ' ').title()
            markdown.append(f"## {header}\n")
            markdown.append(content)
            markdown.append("\n")
        
        return '\n'.join(markdown)
    
    def export_sections(self, sections: Dict[str, str], output_dir: Path):
        """
        Export each section to separate file
        
        Args:
            sections: Dictionary of section content
            output_dir: Directory to save section files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for section_name, content in sections.items():
            filename = f"{section_name}.txt"
            filepath = output_dir / filename
            filepath.write_text(content, encoding='utf-8')
            logger.info(f"Exported section '{section_name}' to {filepath}")
