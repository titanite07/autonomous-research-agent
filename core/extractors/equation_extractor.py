"""
Equation Extractor - Extract mathematical equations from PDFs
"""
from pathlib import Path
from typing import List, Dict, Optional
import logging
import re

logger = logging.getLogger(__name__)


class EquationExtractor:
    """Extract mathematical equations from PDF files"""
    
    def __init__(self):
        """Initialize equation extractor"""
        logger.info("EquationExtractor initialized")
    
    def extract_equations(self, pdf_path: Path) -> List[Dict]:
        """
        Extract equations from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of dictionaries containing equation data and metadata
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.error("PyMuPDF not installed. Install with: pip install pymupdf")
            return []
        
        try:
            logger.info(f"Extracting equations from {pdf_path}")
            
            doc = fitz.open(str(pdf_path))
            equations = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                page_equations = self._extract_from_text(text, page_num + 1)
                equations.extend(page_equations)
            
            doc.close()
            logger.info(f"Extracted {len(equations)} equations from {len(doc)} pages")
            
            return equations
        
        except Exception as e:
            logger.error(f"Error extracting equations: {e}")
            return []
    
    def _extract_from_text(self, text: str, page_num: int) -> List[Dict]:
        """Extract equations from text using patterns"""
        equations = []
        
        # Pattern 1: LaTeX-style equations between $...$ or $$...$$
        latex_patterns = [
            r'\$\$(.*?)\$\$',  # Display equations
            r'\$(.*?)\$',      # Inline equations
        ]
        
        for pattern in latex_patterns:
            matches = re.finditer(pattern, text, re.DOTALL)
            for match in matches:
                equation_text = match.group(1).strip()
                
                if self._is_valid_equation(equation_text):
                    equation_data = {
                        'equation_number': len(equations) + 1,
                        'page': page_num,
                        'type': 'display' if pattern.startswith(r'\$\$') else 'inline',
                        'latex': equation_text,
                        'text': self._latex_to_text(equation_text),
                        'position': match.start(),
                        'length': len(equation_text)
                    }
                    equations.append(equation_data)
        
        # Pattern 2: Common mathematical symbols and expressions
        math_patterns = [
            r'(?:^|\n)\s*([a-zA-Z]\s*=\s*[^\n]+)',  # Variable assignments
            r'∫[^\n]+',  # Integrals
            r'∑[^\n]+',  # Summations
            r'∏[^\n]+',  # Products
            r'lim[^\n]+',  # Limits
            r'∂[^\n]+',  # Partial derivatives
            r'∇[^\n]+',  # Gradients
        ]
        
        for pattern in math_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                equation_text = match.group(0).strip()
                
                if self._is_valid_equation(equation_text) and equation_text not in [eq['text'] for eq in equations]:
                    equation_data = {
                        'equation_number': len(equations) + 1,
                        'page': page_num,
                        'type': 'mathematical_expression',
                        'latex': self._text_to_latex(equation_text),
                        'text': equation_text,
                        'position': match.start(),
                        'length': len(equation_text)
                    }
                    equations.append(equation_data)
        
        return equations
    
    def _is_valid_equation(self, text: str) -> bool:
        """Check if text is likely a valid equation"""
        if not text or len(text) < 3:
            return False
        
        # Must contain mathematical symbols or operators
        math_indicators = ['=', '+', '-', '*', '/', '^', '_', '∫', '∑', '∏', '∂', '∇', 
                          'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'theta',
                          'frac', 'sqrt', 'sum', 'int', 'lim']
        
        return any(indicator in text.lower() for indicator in math_indicators)
    
    def _latex_to_text(self, latex: str) -> str:
        """Convert LaTeX to readable text (simplified)"""
        text = latex
        
        # Common LaTeX commands
        replacements = {
            r'\frac{([^}]+)}{([^}]+)}': r'(\1)/(\2)',
            r'\sqrt{([^}]+)}': r'sqrt(\1)',
            r'\sum': '∑',
            r'\int': '∫',
            r'\prod': '∏',
            r'\partial': '∂',
            r'\nabla': '∇',
            r'\alpha': 'α',
            r'\beta': 'β',
            r'\gamma': 'γ',
            r'\delta': 'δ',
            r'\epsilon': 'ε',
            r'\theta': 'θ',
            r'\lambda': 'λ',
            r'\mu': 'μ',
            r'\sigma': 'σ',
            r'\pi': 'π',
            r'\infty': '∞',
            r'\leq': '≤',
            r'\geq': '≥',
            r'\neq': '≠',
            r'\approx': '≈',
            r'\times': '×',
            r'\cdot': '·',
        }
        
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)
        
        # Remove remaining backslashes
        text = text.replace('\\', '')
        
        # Clean up spaces
        text = ' '.join(text.split())
        
        return text
    
    def _text_to_latex(self, text: str) -> str:
        """Convert text to LaTeX format (basic)"""
        latex = text
        
        # Unicode to LaTeX
        unicode_to_latex = {
            '∫': r'\int',
            '∑': r'\sum',
            '∏': r'\prod',
            '∂': r'\partial',
            '∇': r'\nabla',
            'α': r'\alpha',
            'β': r'\beta',
            'γ': r'\gamma',
            'δ': r'\delta',
            'ε': r'\epsilon',
            'θ': r'\theta',
            'λ': r'\lambda',
            'μ': r'\mu',
            'σ': r'\sigma',
            'π': r'\pi',
            '∞': r'\infty',
            '≤': r'\leq',
            '≥': r'\geq',
            '≠': r'\neq',
            '≈': r'\approx',
            '×': r'\times',
            '·': r'\cdot',
        }
        
        for unicode_char, latex_cmd in unicode_to_latex.items():
            latex = latex.replace(unicode_char, latex_cmd)
        
        return latex
    
    def analyze_equation(self, equation_dict: Dict) -> Dict:
        """
        Analyze equation characteristics
        
        Args:
            equation_dict: Equation dictionary from extract_equations
            
        Returns:
            Analysis results
        """
        text = equation_dict['text']
        latex = equation_dict['latex']
        
        analysis = {
            'length': len(text),
            'complexity': self._estimate_complexity(text),
            'type': equation_dict['type'],
            'page': equation_dict['page'],
            'has_fractions': 'frac' in latex or '/' in text,
            'has_integrals': '∫' in text or 'int' in latex,
            'has_summations': '∑' in text or 'sum' in latex,
            'has_greek_letters': any(c in latex for c in ['alpha', 'beta', 'gamma', 'delta', 'theta']),
            'operator_count': sum(text.count(op) for op in ['+', '-', '*', '/', '='])
        }
        
        return analysis
    
    def _estimate_complexity(self, text: str) -> str:
        """Estimate equation complexity"""
        score = 0
        
        # Count operators
        score += sum(text.count(op) for op in ['+', '-', '*', '/', '^', '='])
        
        # Count special functions
        score += sum(2 for func in ['sqrt', 'int', 'sum', 'lim', 'frac'] if func in text.lower())
        
        # Count Greek letters
        score += len(re.findall(r'[α-ωΑ-Ω]', text))
        
        # Determine complexity
        if score < 5:
            return 'simple'
        elif score < 15:
            return 'moderate'
        else:
            return 'complex'
    
    def filter_equations(self,
                        equations: List[Dict],
                        min_length: int = 5,
                        equation_type: Optional[str] = None) -> List[Dict]:
        """
        Filter equations by criteria
        
        Args:
            equations: List of equation dictionaries
            min_length: Minimum equation length
            equation_type: Type filter ('inline', 'display', 'mathematical_expression')
            
        Returns:
            Filtered list of equations
        """
        filtered = []
        
        for equation in equations:
            if len(equation['text']) < min_length:
                continue
            
            if equation_type and equation['type'] != equation_type:
                continue
            
            filtered.append(equation)
        
        logger.info(f"Filtered {len(filtered)}/{len(equations)} equations")
        return filtered
    
    def group_by_page(self, equations: List[Dict]) -> Dict[int, List[Dict]]:
        """Group equations by page number"""
        grouped = {}
        
        for equation in equations:
            page = equation['page']
            if page not in grouped:
                grouped[page] = []
            grouped[page].append(equation)
        
        return grouped
