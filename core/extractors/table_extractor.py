"""
Table Extractor - Extract tables from PDFs using Camelot
"""
from pathlib import Path
from typing import List, Dict, Optional
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class TableExtractor:
    """Extract tables from PDF files using Camelot"""
    
    def __init__(self, flavor: str = 'lattice'):
        """
        Initialize table extractor
        
        Args:
            flavor: Extraction method ('lattice' for bordered tables, 'stream' for borderless)
        """
        self.flavor = flavor
        logger.info(f"TableExtractor initialized with flavor: {flavor}")
    
    def extract_tables(self, 
                      pdf_path: Path, 
                      pages: str = 'all',
                      min_accuracy: float = 80.0) -> List[Dict]:
        """
        Extract tables from PDF
        
        Args:
            pdf_path: Path to PDF file
            pages: Pages to extract from ('all', '1', '1,2,3', '1-5')
            min_accuracy: Minimum accuracy threshold (0-100)
            
        Returns:
            List of dictionaries containing table data and metadata
        """
        try:
            import camelot
        except ImportError as e:
            logger.error("Camelot not installed. Install with: pip install camelot-py[cv]")
            logger.error("Also requires: pip install ghostscript opencv-python")
            return []
        
        try:
            logger.info(f"Extracting tables from {pdf_path} (pages: {pages}, flavor: {self.flavor})")
            
            # Extract tables using Camelot
            tables = camelot.read_pdf(
                str(pdf_path),
                pages=pages,
                flavor=self.flavor,
                suppress_stdout=True
            )
            
            logger.info(f"Found {len(tables)} tables")
            
            # Process tables
            extracted_tables = []
            for i, table in enumerate(tables):
                # Check accuracy
                accuracy = table.parsing_report.get('accuracy', 0)
                
                if accuracy < min_accuracy:
                    logger.debug(f"Table {i+1} accuracy {accuracy:.2f}% below threshold {min_accuracy}%")
                    continue
                
                # Convert to pandas DataFrame
                df = table.df
                
                # Get table metadata
                table_data = {
                    'table_number': i + 1,
                    'page': table.page,
                    'accuracy': accuracy,
                    'dataframe': df,
                    'shape': df.shape,
                    'whitespace': table.parsing_report.get('whitespace', 0),
                    'text': self._table_to_text(df),
                    'csv': df.to_csv(index=False),
                    'json': df.to_json(orient='records'),
                    'markdown': self._table_to_markdown(df)
                }
                
                extracted_tables.append(table_data)
                logger.info(f"Extracted table {i+1} (page {table.page}): {df.shape} - accuracy: {accuracy:.2f}%")
            
            return extracted_tables
        
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            return []
    
    def extract_tables_stream(self, pdf_path: Path, pages: str = 'all') -> List[Dict]:
        """
        Extract borderless tables using stream flavor
        
        Args:
            pdf_path: Path to PDF file
            pages: Pages to extract from
            
        Returns:
            List of table dictionaries
        """
        old_flavor = self.flavor
        self.flavor = 'stream'
        try:
            return self.extract_tables(pdf_path, pages)
        finally:
            self.flavor = old_flavor
    
    def extract_tables_auto(self, pdf_path: Path, pages: str = 'all') -> List[Dict]:
        """
        Automatically try both lattice and stream flavors
        
        Args:
            pdf_path: Path to PDF file
            pages: Pages to extract from
            
        Returns:
            Combined list of tables from both methods
        """
        logger.info("Extracting tables with auto mode (lattice + stream)")
        
        # Try lattice first (works better for bordered tables)
        lattice_tables = self.extract_tables(pdf_path, pages)
        
        # Try stream (works better for borderless tables)
        stream_tables = self.extract_tables_stream(pdf_path, pages)
        
        # Combine results (deduplicate by page and position)
        all_tables = lattice_tables + stream_tables
        
        # Sort by page and table number
        all_tables.sort(key=lambda x: (x['page'], x['table_number']))
        
        logger.info(f"Auto mode found {len(all_tables)} total tables "
                   f"(lattice: {len(lattice_tables)}, stream: {len(stream_tables)})")
        
        return all_tables
    
    def _table_to_text(self, df: pd.DataFrame) -> str:
        """Convert DataFrame to readable text"""
        return df.to_string(index=False)
    
    def _table_to_markdown(self, df: pd.DataFrame) -> str:
        """Convert DataFrame to Markdown table"""
        return df.to_markdown(index=False)
    
    def save_tables(self, tables: List[Dict], output_dir: Path):
        """
        Save extracted tables to files
        
        Args:
            tables: List of table dictionaries
            output_dir: Directory to save tables
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for table in tables:
            table_num = table['table_number']
            page = table['page']
            df = table['dataframe']
            
            # Save in multiple formats
            base_name = f"table_{page}_{table_num}"
            
            # CSV
            csv_path = output_dir / f"{base_name}.csv"
            df.to_csv(csv_path, index=False)
            
            # Excel
            excel_path = output_dir / f"{base_name}.xlsx"
            df.to_excel(excel_path, index=False, engine='openpyxl')
            
            # Markdown
            md_path = output_dir / f"{base_name}.md"
            md_path.write_text(table['markdown'])
            
            logger.info(f"Saved table {table_num} from page {page} to {output_dir}")
    
    def analyze_table(self, table_dict: Dict) -> Dict:
        """
        Analyze table characteristics
        
        Args:
            table_dict: Table dictionary from extract_tables
            
        Returns:
            Analysis results
        """
        df = table_dict['dataframe']
        
        analysis = {
            'rows': df.shape[0],
            'columns': df.shape[1],
            'accuracy': table_dict['accuracy'],
            'page': table_dict['page'],
            'has_headers': self._detect_headers(df),
            'numeric_columns': len(df.select_dtypes(include=['number']).columns),
            'text_columns': len(df.select_dtypes(include=['object']).columns),
            'empty_cells': df.isna().sum().sum(),
            'completeness': (1 - df.isna().sum().sum() / (df.shape[0] * df.shape[1])) * 100
        }
        
        return analysis
    
    def _detect_headers(self, df: pd.DataFrame) -> bool:
        """Detect if first row contains headers"""
        if df.empty:
            return False
        
        # Check if first row has different characteristics than rest
        first_row = df.iloc[0]
        rest = df.iloc[1:]
        
        # Simple heuristic: headers are usually text, data is often numeric
        first_row_text = sum(isinstance(x, str) for x in first_row)
        return first_row_text > len(first_row) * 0.5
    
    def filter_tables(self, 
                     tables: List[Dict],
                     min_rows: int = 2,
                     min_cols: int = 2,
                     min_accuracy: float = 70.0) -> List[Dict]:
        """
        Filter tables by quality criteria
        
        Args:
            tables: List of table dictionaries
            min_rows: Minimum number of rows
            min_cols: Minimum number of columns
            min_accuracy: Minimum accuracy percentage
            
        Returns:
            Filtered list of tables
        """
        filtered = []
        
        for table in tables:
            df = table['dataframe']
            accuracy = table['accuracy']
            
            if (df.shape[0] >= min_rows and 
                df.shape[1] >= min_cols and 
                accuracy >= min_accuracy):
                filtered.append(table)
            else:
                logger.debug(f"Filtered out table {table['table_number']}: "
                           f"shape={df.shape}, accuracy={accuracy:.2f}%")
        
        logger.info(f"Filtered {len(filtered)}/{len(tables)} tables")
        return filtered
