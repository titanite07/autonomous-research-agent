"""
PDF Manager - Downloads and extracts text from academic PDFs
"""
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, Dict
import logging
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)


class PDFManager:
    """Manages PDF downloading and text extraction"""
    
    def __init__(self, cache_dir: str = "./pdf_cache"):
        """
        Initialize PDF Manager
        
        Args:
            cache_dir: Directory to cache downloaded PDFs
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"PDFManager initialized with cache: {cache_dir}")
    
    def _get_cache_path(self, paper_id: str) -> Path:
        """Get cache file path for a paper"""
        # Use paper ID hash for filename
        filename = hashlib.md5(paper_id.encode()).hexdigest() + ".pdf"
        return self.cache_dir / filename
    
    async def download_pdf(self, url: str, paper_id: str, timeout: int = 30) -> Optional[Path]:
        """
        Download PDF from URL
        
        Args:
            url: PDF download URL
            paper_id: Unique paper identifier
            timeout: Download timeout in seconds
            
        Returns:
            Path to downloaded PDF or None if failed
        """
        cache_path = self._get_cache_path(paper_id)
        
        # Check cache first
        if cache_path.exists():
            logger.info(f"PDF already cached: {paper_id}")
            return cache_path
        
        try:
            logger.info(f"Downloading PDF: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Save to cache
                        with open(cache_path, 'wb') as f:
                            f.write(content)
                        
                        logger.info(f"PDF downloaded successfully: {paper_id} ({len(content)} bytes)")
                        return cache_path
                    else:
                        logger.warning(f"Failed to download PDF: HTTP {response.status}")
                        return None
        
        except asyncio.TimeoutError:
            logger.warning(f"PDF download timeout: {url}")
            return None
        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            return None
    
    def extract_text(self, pdf_path: Path) -> Optional[str]:
        """
        Extract text from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text or None if failed
        """
        try:
            import pypdf2
            
            with open(pdf_path, 'rb') as f:
                pdf_reader = pypdf2.PdfReader(f)
                
                text_parts = []
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_parts.append(page.extract_text())
                
                full_text = "\n\n".join(text_parts)
                logger.info(f"Extracted {len(full_text)} characters from PDF")
                
                return full_text
        
        except ImportError:
            logger.error("pypdf2 not installed. Install with: pip install pypdf2")
            return None
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return None
    
    def extract_text_pdfplumber(self, pdf_path: Path) -> Optional[str]:
        """
        Extract text from PDF using pdfplumber (better quality)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text or None if failed
        """
        try:
            import pdfplumber
            
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            
            full_text = "\n\n".join(text_parts)
            logger.info(f"Extracted {len(full_text)} characters from PDF (pdfplumber)")
            
            return full_text
        
        except ImportError:
            logger.warning("pdfplumber not installed. Falling back to pypdf2. Install with: pip install pdfplumber")
            return self.extract_text(pdf_path)
        except Exception as e:
            logger.error(f"Error extracting text with pdfplumber: {e}")
            # Fallback to pypdf2
            return self.extract_text(pdf_path)
    
    async def get_full_text(self, paper: Dict) -> Optional[str]:
        """
        Get full text of paper (download if needed)
        
        Args:
            paper: Paper dictionary with pdf_url and paper_id
            
        Returns:
            Full text of paper or None if unavailable
        """
        pdf_url = paper.get('pdf_url')
        paper_id = paper.get('paper_id')
        
        if not pdf_url or not paper_id:
            logger.warning("Paper missing PDF URL or ID")
            return None
        
        # Download PDF
        pdf_path = await self.download_pdf(pdf_url, paper_id)
        
        if not pdf_path:
            logger.warning(f"Could not download PDF for paper: {paper_id}")
            return None
        
        # Extract text (prefer pdfplumber for better quality)
        text = self.extract_text_pdfplumber(pdf_path)
        
        return text
    
    def get_cache_stats(self) -> Dict:
        """Get statistics about the PDF cache"""
        try:
            pdf_files = list(self.cache_dir.glob("*.pdf"))
            total_size = sum(f.stat().st_size for f in pdf_files)
            
            return {
                'total_pdfs': len(pdf_files),
                'total_size_mb': total_size / (1024 * 1024),
                'cache_directory': str(self.cache_dir)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                'total_pdfs': 0,
                'total_size_mb': 0,
                'error': str(e)
            }
    
    def clear_cache(self, older_than_days: Optional[int] = None):
        """
        Clear PDF cache
        
        Args:
            older_than_days: Only clear PDFs older than this many days (None = clear all)
        """
        try:
            pdf_files = list(self.cache_dir.glob("*.pdf"))
            removed_count = 0
            
            for pdf_file in pdf_files:
                if older_than_days:
                    # Check file age
                    mtime = datetime.fromtimestamp(pdf_file.stat().st_mtime)
                    age_days = (datetime.now() - mtime).days
                    
                    if age_days < older_than_days:
                        continue
                
                pdf_file.unlink()
                removed_count += 1
            
            logger.info(f"Cleared {removed_count} PDFs from cache")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")


async def download_papers_batch(pdf_manager: PDFManager, papers: list) -> Dict[str, str]:
    """
    Download multiple papers concurrently
    
    Args:
        pdf_manager: PDFManager instance
        papers: List of paper dictionaries
        
    Returns:
        Dictionary mapping paper_id to full text
    """
    tasks = []
    for paper in papers:
        task = pdf_manager.get_full_text(paper)
        tasks.append((paper.get('paper_id'), task))
    
    results = {}
    completed_tasks = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
    
    for (paper_id, _), result in zip(tasks, completed_tasks):
        if isinstance(result, Exception):
            logger.error(f"Error downloading paper {paper_id}: {result}")
            results[paper_id] = None
        else:
            results[paper_id] = result
    
    return results
