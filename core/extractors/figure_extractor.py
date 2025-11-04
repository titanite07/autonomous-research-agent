"""
Figure Extractor - Extract figures and images from PDFs with OCR
"""
from pathlib import Path
from typing import List, Dict, Optional
import logging
from PIL import Image
import io

logger = logging.getLogger(__name__)


class FigureExtractor:
    """Extract figures, images, and diagrams from PDF files"""
    
    def __init__(self, dpi: int = 300, ocr_enabled: bool = True):
        """
        Initialize figure extractor
        
        Args:
            dpi: Resolution for image extraction
            ocr_enabled: Whether to perform OCR on extracted figures
        """
        self.dpi = dpi
        self.ocr_enabled = ocr_enabled
        logger.info(f"FigureExtractor initialized (DPI: {dpi}, OCR: {ocr_enabled})")
    
    def extract_figures(self, pdf_path: Path, output_dir: Optional[Path] = None) -> List[Dict]:
        """
        Extract all figures from PDF
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Optional directory to save extracted images
            
        Returns:
            List of dictionaries containing figure data and metadata
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.error("PyMuPDF not installed. Install with: pip install pymupdf")
            return []
        
        try:
            logger.info(f"Extracting figures from {pdf_path}")
            
            doc = fitz.open(str(pdf_path))
            figures = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_figures = self._extract_from_page(page, page_num + 1, output_dir)
                figures.extend(page_figures)
            
            doc.close()
            logger.info(f"Extracted {len(figures)} figures from {len(doc)} pages")
            
            return figures
        
        except Exception as e:
            logger.error(f"Error extracting figures: {e}")
            return []
    
    def _extract_from_page(self, page, page_num: int, output_dir: Optional[Path]) -> List[Dict]:
        """Extract figures from a single page"""
        import fitz
        
        figures = []
        
        # Get all images on the page
        image_list = page.get_images(full=True)
        
        for img_idx, img_info in enumerate(image_list):
            try:
                xref = img_info[0]
                base_image = page.parent.extract_image(xref)
                
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(image_bytes))
                
                # Get image properties
                width, height = image.size
                
                # Skip small images (likely logos or icons)
                if width < 100 or height < 100:
                    continue
                
                figure_data = {
                    'figure_number': len(figures) + 1,
                    'page': page_num,
                    'width': width,
                    'height': height,
                    'format': image_ext,
                    'size_bytes': len(image_bytes),
                    'image': image,
                    'xref': xref
                }
                
                # Perform OCR if enabled
                if self.ocr_enabled:
                    ocr_text = self._perform_ocr(image)
                    figure_data['ocr_text'] = ocr_text
                    figure_data['has_text'] = len(ocr_text.strip()) > 0
                
                # Try to find caption
                caption = self._find_caption(page, page_num)
                figure_data['caption'] = caption
                
                # Save image if output directory provided
                if output_dir:
                    output_dir = Path(output_dir)
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    img_filename = f"figure_page{page_num}_{len(figures)+1}.{image_ext}"
                    img_path = output_dir / img_filename
                    image.save(img_path)
                    figure_data['saved_path'] = str(img_path)
                
                figures.append(figure_data)
                logger.debug(f"Extracted figure {len(figures)} from page {page_num}: {width}x{height}")
            
            except Exception as e:
                logger.warning(f"Failed to extract image {img_idx} from page {page_num}: {e}")
                continue
        
        return figures
    
    def _perform_ocr(self, image: Image.Image) -> str:
        """Perform OCR on image using Tesseract"""
        if not self.ocr_enabled:
            return ""
        
        try:
            import pytesseract
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Perform OCR
            text = pytesseract.image_to_string(image)
            return text.strip()
        
        except ImportError:
            logger.warning("Tesseract not available. Install with: pip install pytesseract")
            self.ocr_enabled = False
            return ""
        except Exception as e:
            logger.warning(f"OCR failed: {e}")
            return ""
    
    def _find_caption(self, page, page_num: int) -> str:
        """
        Try to find figure caption on the page
        
        This is a simple heuristic - looks for text containing 'Figure' or 'Fig.'
        """
        try:
            text = page.get_text()
            lines = text.split('\n')
            
            # Look for lines starting with "Figure" or "Fig."
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                if line_lower.startswith(('figure', 'fig.')):
                    # Get caption (current line + next few lines)
                    caption_lines = [line]
                    for j in range(1, min(3, len(lines) - i)):
                        next_line = lines[i + j].strip()
                        if next_line and not next_line.lower().startswith(('figure', 'fig.', 'table')):
                            caption_lines.append(next_line)
                        else:
                            break
                    
                    return ' '.join(caption_lines)
            
            return ""
        
        except Exception as e:
            logger.debug(f"Caption detection failed: {e}")
            return ""
    
    def analyze_figure(self, figure_dict: Dict) -> Dict:
        """
        Analyze figure characteristics
        
        Args:
            figure_dict: Figure dictionary from extract_figures
            
        Returns:
            Analysis results
        """
        image = figure_dict['image']
        
        analysis = {
            'width': figure_dict['width'],
            'height': figure_dict['height'],
            'aspect_ratio': figure_dict['width'] / figure_dict['height'],
            'format': figure_dict['format'],
            'size_kb': figure_dict['size_bytes'] / 1024,
            'page': figure_dict['page'],
            'has_caption': len(figure_dict.get('caption', '')) > 0,
            'has_text': figure_dict.get('has_text', False),
            'is_color': image.mode in ['RGB', 'RGBA'],
            'is_large': figure_dict['width'] > 800 or figure_dict['height'] > 800
        }
        
        return analysis
    
    def filter_figures(self,
                      figures: List[Dict],
                      min_width: int = 200,
                      min_height: int = 200,
                      max_size_mb: float = 10.0) -> List[Dict]:
        """
        Filter figures by quality criteria
        
        Args:
            figures: List of figure dictionaries
            min_width: Minimum width in pixels
            min_height: Minimum height in pixels
            max_size_mb: Maximum file size in MB
            
        Returns:
            Filtered list of figures
        """
        filtered = []
        max_size_bytes = max_size_mb * 1024 * 1024
        
        for figure in figures:
            if (figure['width'] >= min_width and
                figure['height'] >= min_height and
                figure['size_bytes'] <= max_size_bytes):
                filtered.append(figure)
            else:
                logger.debug(f"Filtered out figure {figure['figure_number']}: "
                           f"size={figure['width']}x{figure['height']}, "
                           f"bytes={figure['size_bytes']}")
        
        logger.info(f"Filtered {len(filtered)}/{len(figures)} figures")
        return filtered
    
    def extract_figure_by_caption(self, 
                                  pdf_path: Path,
                                  caption_keyword: str,
                                  output_dir: Optional[Path] = None) -> Optional[Dict]:
        """
        Extract specific figure by searching for caption keyword
        
        Args:
            pdf_path: Path to PDF file
            caption_keyword: Keyword to search in captions (e.g., "Figure 1")
            output_dir: Optional directory to save image
            
        Returns:
            Figure dictionary if found, None otherwise
        """
        figures = self.extract_figures(pdf_path, output_dir)
        
        for figure in figures:
            caption = figure.get('caption', '').lower()
            if caption_keyword.lower() in caption:
                logger.info(f"Found figure with caption containing '{caption_keyword}'")
                return figure
        
        logger.warning(f"No figure found with caption containing '{caption_keyword}'")
        return None
    
    def convert_to_format(self, 
                         figure_dict: Dict,
                         output_path: Path,
                         format: str = 'PNG',
                         quality: int = 95):
        """
        Convert figure to different format
        
        Args:
            figure_dict: Figure dictionary from extract_figures
            output_path: Path to save converted image
            format: Target format (PNG, JPEG, TIFF, etc.)
            quality: Quality for lossy formats (1-100)
        """
        try:
            image = figure_dict['image']
            
            # Convert mode if necessary
            if format.upper() == 'JPEG' and image.mode in ['RGBA', 'LA', 'P']:
                image = image.convert('RGB')
            
            # Save with specified format
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.upper() in ['JPEG', 'JPG']:
                image.save(output_path, format='JPEG', quality=quality, optimize=True)
            else:
                image.save(output_path, format=format)
            
            logger.info(f"Converted figure to {format} at {output_path}")
        
        except Exception as e:
            logger.error(f"Failed to convert figure: {e}")
