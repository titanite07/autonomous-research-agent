"""PyMuPDF (fitz) PDF processor for extracting text and metadata from PDFs."""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import io

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    fitz = None

logger = logging.getLogger(__name__)


class PyMuPDFProcessor:
    """
    PDF processor using PyMuPDF (fitz) library.
    Fast and efficient for text extraction and basic layout analysis.
    """
    
    def __init__(self):
        """Initialize PyMuPDF processor."""
        if not PYMUPDF_AVAILABLE:
            logger.warning("PyMuPDF not installed. Install with: pip install PyMuPDF")
            raise ImportError("PyMuPDF is required but not installed")
        
        self.logger = logger
    
    def extract_text(self, pdf_path: str) -> str:
        """
        Extract plain text from PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text += page.get_text()
            
            doc.close()
            
            logger.info(f"Extracted text from {len(doc)} pages")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""
    
    def extract_with_structure(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text with structure (pages, sections).
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with structured content
        """
        try:
            doc = fitz.open(pdf_path)
            
            result = {
                'metadata': self._extract_metadata(doc),
                'pages': [],
                'full_text': '',
                'num_pages': len(doc)
            }
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                
                page_data = {
                    'page_number': page_num + 1,
                    'text': page_text,
                    'width': page.rect.width,
                    'height': page.rect.height
                }
                
                result['pages'].append(page_data)
                result['full_text'] += page_text + '\n\n'
            
            doc.close()
            
            logger.info(f"Extracted structured content from {len(doc)} pages")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting structured content: {e}")
            return {}
    
    def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract PDF metadata.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with metadata
        """
        try:
            doc = fitz.open(pdf_path)
            metadata = self._extract_metadata(doc)
            doc.close()
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}
    
    def _extract_metadata(self, doc) -> Dict[str, Any]:
        """Extract metadata from open document."""
        metadata = {}
        
        try:
            # Get PDF metadata
            pdf_metadata = doc.metadata
            
            if pdf_metadata:
                metadata['title'] = pdf_metadata.get('title', '')
                metadata['author'] = pdf_metadata.get('author', '')
                metadata['subject'] = pdf_metadata.get('subject', '')
                metadata['keywords'] = pdf_metadata.get('keywords', '')
                metadata['creator'] = pdf_metadata.get('creator', '')
                metadata['producer'] = pdf_metadata.get('producer', '')
                metadata['creation_date'] = pdf_metadata.get('creationDate', '')
                metadata['mod_date'] = pdf_metadata.get('modDate', '')
            
            metadata['page_count'] = len(doc)
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
        
        return metadata
    
    def extract_images(self, pdf_path: str, output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract images from PDF.
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Optional directory to save images
            
        Returns:
            List of image information dictionaries
        """
        images = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    
                    image_info = {
                        'page': page_num + 1,
                        'index': img_index,
                        'width': base_image['width'],
                        'height': base_image['height'],
                        'format': base_image['ext'],
                        'size': len(base_image['image'])
                    }
                    
                    # Save image if output directory provided
                    if output_dir:
                        output_path = Path(output_dir)
                        output_path.mkdir(parents=True, exist_ok=True)
                        
                        image_filename = output_path / f"page{page_num+1}_img{img_index}.{base_image['ext']}"
                        with open(image_filename, 'wb') as f:
                            f.write(base_image['image'])
                        
                        image_info['saved_path'] = str(image_filename)
                    
                    images.append(image_info)
            
            doc.close()
            
            logger.info(f"Extracted {len(images)} images from PDF")
            
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
        
        return images
    
    def extract_tables(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract tables from PDF (basic implementation).
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of table dictionaries
        """
        tables = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Get text blocks
                blocks = page.get_text("dict")["blocks"]
                
                # Simple table detection based on alignment
                # (This is basic - for better table extraction, use specialized libraries)
                for block in blocks:
                    if "lines" in block:
                        table_data = {
                            'page': page_num + 1,
                            'bbox': block.get('bbox'),
                            'text': block.get('text', '')
                        }
                        tables.append(table_data)
            
            doc.close()
            
            logger.info(f"Detected {len(tables)} potential table regions")
            
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
        
        return tables
    
    def get_toc(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract table of contents from PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of TOC entries
        """
        try:
            doc = fitz.open(pdf_path)
            toc = doc.get_toc()
            doc.close()
            
            # Convert to structured format
            structured_toc = []
            for item in toc:
                level, title, page = item
                structured_toc.append({
                    'level': level,
                    'title': title,
                    'page': page
                })
            
            logger.info(f"Extracted TOC with {len(structured_toc)} entries")
            return structured_toc
            
        except Exception as e:
            logger.error(f"Error extracting TOC: {e}")
            return []
    
    def search_text(self, pdf_path: str, query: str) -> List[Dict[str, Any]]:
        """
        Search for text in PDF.
        
        Args:
            pdf_path: Path to PDF file
            query: Search query
            
        Returns:
            List of search results with page numbers and positions
        """
        results = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text_instances = page.search_for(query)
                
                for inst in text_instances:
                    results.append({
                        'page': page_num + 1,
                        'bbox': inst,
                        'query': query
                    })
            
            doc.close()
            
            logger.info(f"Found {len(results)} instances of '{query}'")
            
        except Exception as e:
            logger.error(f"Error searching text: {e}")
        
        return results
