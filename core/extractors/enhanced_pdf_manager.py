"""
Enhanced PDF Manager - Integrates all extraction capabilities
"""
from pathlib import Path
from typing import Dict, List, Optional
import logging

from .table_extractor import TableExtractor
from .figure_extractor import FigureExtractor
from .equation_extractor import EquationExtractor
from .section_parser import SectionParser

logger = logging.getLogger(__name__)


class EnhancedPDFManager:
    """Enhanced PDF manager with table, figure, equation, and section extraction"""
    
    def __init__(self, cache_dir: str = "pdf_cache"):
        """
        Initialize enhanced PDF manager
        
        Args:
            cache_dir: Directory for caching PDFs and extracted content
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize extractors
        self.table_extractor = TableExtractor()
        self.figure_extractor = FigureExtractor()
        self.equation_extractor = EquationExtractor()
        self.section_parser = SectionParser()
        
        logger.info(f"EnhancedPDFManager initialized with cache: {cache_dir}")
    
    def extract_all(self, pdf_path: Path) -> Dict:
        """
        Extract all content from PDF (tables, figures, equations, sections)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary containing all extracted content
        """
        logger.info(f"Extracting all content from {pdf_path}")
        
        result = {
            'pdf_path': str(pdf_path),
            'tables': [],
            'figures': [],
            'equations': [],
            'sections': {},
            'metadata': {}
        }
        
        try:
            # Extract tables
            logger.info("Extracting tables...")
            result['tables'] = self.table_extractor.extract_tables_auto(pdf_path)
            logger.info(f"Found {len(result['tables'])} tables")
            
            # Extract figures
            logger.info("Extracting figures...")
            figures_dir = self.cache_dir / "figures" / pdf_path.stem
            result['figures'] = self.figure_extractor.extract_figures(pdf_path, figures_dir)
            logger.info(f"Found {len(result['figures'])} figures")
            
            # Extract equations
            logger.info("Extracting equations...")
            result['equations'] = self.equation_extractor.extract_equations(pdf_path)
            logger.info(f"Found {len(result['equations'])} equations")
            
            # Parse sections
            logger.info("Parsing sections...")
            result['sections'] = self.section_parser.parse_sections(pdf_path)
            logger.info(f"Found {len(result['sections'])} sections")
            
            # Get metadata
            result['metadata'] = self._get_metadata(result)
            
            logger.info("Extraction complete")
            return result
        
        except Exception as e:
            logger.error(f"Error during extraction: {e}")
            return result
    
    def extract_tables_only(self, pdf_path: Path, **kwargs) -> List[Dict]:
        """Extract only tables from PDF"""
        return self.table_extractor.extract_tables(pdf_path, **kwargs)
    
    def extract_figures_only(self, pdf_path: Path, **kwargs) -> List[Dict]:
        """Extract only figures from PDF"""
        return self.figure_extractor.extract_figures(pdf_path, **kwargs)
    
    def extract_equations_only(self, pdf_path: Path) -> List[Dict]:
        """Extract only equations from PDF"""
        return self.equation_extractor.extract_equations(pdf_path)
    
    def parse_sections_only(self, pdf_path: Path) -> Dict[str, str]:
        """Parse only sections from PDF"""
        return self.section_parser.parse_sections(pdf_path)
    
    def _get_metadata(self, extraction_result: Dict) -> Dict:
        """Get metadata about extraction"""
        return {
            'total_tables': len(extraction_result['tables']),
            'total_figures': len(extraction_result['figures']),
            'total_equations': len(extraction_result['equations']),
            'total_sections': len(extraction_result['sections']),
            'table_pages': [t['page'] for t in extraction_result['tables']],
            'figure_pages': [f['page'] for f in extraction_result['figures']],
            'equation_pages': list(set(eq['page'] for eq in extraction_result['equations'])),
            'sections_found': list(extraction_result['sections'].keys())
        }
    
    def get_summary(self, extraction_result: Dict) -> str:
        """
        Get human-readable summary of extraction
        
        Args:
            extraction_result: Result from extract_all()
            
        Returns:
            Formatted summary string
        """
        metadata = extraction_result['metadata']
        
        summary = f"""
PDF Extraction Summary
=====================

File: {extraction_result['pdf_path']}

Content Overview:
- Tables: {metadata['total_tables']} found on pages {metadata['table_pages']}
- Figures: {metadata['total_figures']} found on pages {metadata['figure_pages']}
- Equations: {metadata['total_equations']} found on pages {metadata['equation_pages']}
- Sections: {metadata['total_sections']} sections identified

Sections Found:
{self._format_sections_list(extraction_result['sections'])}

Tables Summary:
{self._format_tables_summary(extraction_result['tables'])}

Figures Summary:
{self._format_figures_summary(extraction_result['figures'])}

Equations Summary:
{self._format_equations_summary(extraction_result['equations'])}
"""
        return summary.strip()
    
    def _format_sections_list(self, sections: Dict[str, str]) -> str:
        """Format sections list"""
        if not sections:
            return "  No sections found"
        
        lines = []
        for name, content in sections.items():
            word_count = len(content.split())
            lines.append(f"  - {name.upper()}: {word_count} words")
        return '\n'.join(lines)
    
    def _format_tables_summary(self, tables: List[Dict]) -> str:
        """Format tables summary"""
        if not tables:
            return "  No tables found"
        
        lines = []
        for table in tables:
            shape = table['shape']
            accuracy = table['accuracy']
            lines.append(f"  - Table {table['table_number']} (Page {table['page']}): "
                        f"{shape[0]}x{shape[1]}, accuracy: {accuracy:.1f}%")
        return '\n'.join(lines)
    
    def _format_figures_summary(self, figures: List[Dict]) -> str:
        """Format figures summary"""
        if not figures:
            return "  No figures found"
        
        lines = []
        for figure in figures:
            size = f"{figure['width']}x{figure['height']}"
            has_text = "with text" if figure.get('has_text') else "no text"
            lines.append(f"  - Figure {figure['figure_number']} (Page {figure['page']}): "
                        f"{size}, {has_text}")
        return '\n'.join(lines)
    
    def _format_equations_summary(self, equations: List[Dict]) -> str:
        """Format equations summary"""
        if not equations:
            return "  No equations found"
        
        # Group by type
        by_type = {}
        for eq in equations:
            eq_type = eq['type']
            by_type[eq_type] = by_type.get(eq_type, 0) + 1
        
        lines = []
        for eq_type, count in by_type.items():
            lines.append(f"  - {eq_type}: {count}")
        return '\n'.join(lines)
    
    def export_to_json(self, extraction_result: Dict, output_path: Path):
        """
        Export extraction results to JSON
        
        Args:
            extraction_result: Result from extract_all()
            output_path: Path to save JSON file
        """
        import json
        
        # Convert DataFrames to JSON-serializable format
        serializable_result = extraction_result.copy()
        
        for table in serializable_result['tables']:
            # Remove DataFrame object (already have csv/json)
            if 'dataframe' in table:
                del table['dataframe']
        
        for figure in serializable_result['figures']:
            # Remove PIL Image object
            if 'image' in figure:
                del figure['image']
            # Keep only path if saved
            if 'saved_path' not in figure:
                figure['note'] = 'Image not saved'
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported extraction results to {output_path}")
    
    def export_to_markdown(self, extraction_result: Dict, output_path: Path):
        """
        Export extraction results to Markdown
        
        Args:
            extraction_result: Result from extract_all()
            output_path: Path to save Markdown file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        md_lines = [
            f"# PDF Extraction Report",
            f"",
            f"**File:** `{extraction_result['pdf_path']}`",
            f"",
            f"## Summary",
            f"",
            self.get_summary(extraction_result),
            f"",
            f"## Sections",
            f""
        ]
        
        # Add sections
        for section_name, content in extraction_result['sections'].items():
            md_lines.append(f"### {section_name.upper()}")
            md_lines.append("")
            md_lines.append(content)
            md_lines.append("")
        
        # Add tables
        if extraction_result['tables']:
            md_lines.append(f"## Tables")
            md_lines.append("")
            
            for table in extraction_result['tables']:
                md_lines.append(f"### Table {table['table_number']} (Page {table['page']})")
                md_lines.append("")
                md_lines.append(table['markdown'])
                md_lines.append("")
        
        # Add equations
        if extraction_result['equations']:
            md_lines.append(f"## Equations")
            md_lines.append("")
            
            for eq in extraction_result['equations']:
                md_lines.append(f"**Equation {eq['equation_number']}** (Page {eq['page']}, {eq['type']})")
                md_lines.append(f"```")
                md_lines.append(eq['text'])
                md_lines.append(f"```")
                md_lines.append("")
        
        output_path.write_text('\n'.join(md_lines), encoding='utf-8')
        logger.info(f"Exported extraction results to {output_path}")
    
    def search_content(self, extraction_result: Dict, query: str) -> Dict:
        """
        Search for query across all extracted content
        
        Args:
            extraction_result: Result from extract_all()
            query: Search query
            
        Returns:
            Dictionary with search results
        """
        query_lower = query.lower()
        results = {
            'query': query,
            'tables': [],
            'figures': [],
            'equations': [],
            'sections': []
        }
        
        # Search in tables
        for table in extraction_result['tables']:
            if query_lower in table['text'].lower():
                results['tables'].append(table)
        
        # Search in figure captions and OCR text
        for figure in extraction_result['figures']:
            caption = figure.get('caption', '').lower()
            ocr_text = figure.get('ocr_text', '').lower()
            
            if query_lower in caption or query_lower in ocr_text:
                results['figures'].append(figure)
        
        # Search in equations
        for equation in extraction_result['equations']:
            if query_lower in equation['text'].lower():
                results['equations'].append(equation)
        
        # Search in sections
        for section_name, content in extraction_result['sections'].items():
            if query_lower in content.lower():
                results['sections'].append({
                    'section': section_name,
                    'content_preview': self._get_preview(content, query_lower)
                })
        
        return results
    
    def _get_preview(self, text: str, query: str, context_chars: int = 100) -> str:
        """Get preview of text around query"""
        text_lower = text.lower()
        pos = text_lower.find(query)
        
        if pos == -1:
            return ""
        
        start = max(0, pos - context_chars)
        end = min(len(text), pos + len(query) + context_chars)
        
        preview = text[start:end]
        if start > 0:
            preview = "..." + preview
        if end < len(text):
            preview = preview + "..."
        
        return preview
