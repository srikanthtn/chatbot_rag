#app/utils.py
import logging
from PyPDF2 import PdfReader
from typing import Optional
import os

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file with improved error handling
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    try:
        reader = PdfReader(file_path)
        
        if len(reader.pages) == 0:
            raise ValueError("PDF file is empty or corrupted")
        
        text = ""
        total_pages = len(reader.pages)
        
        for page_num, page in enumerate(reader.pages, 1):
            try:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                else:
                    logger.warning(f"No text extracted from page {page_num}")
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num}: {e}")
                continue
        
        if not text.strip():
            raise ValueError("No text could be extracted from the PDF. It may be scanned or image-based.")
        
        logger.info(f"Successfully extracted text from {total_pages} pages")
        return text.strip()
        
    except Exception as e:
        logger.error(f"Error processing PDF {file_path}: {e}")
        raise

def validate_pdf_file(file_path: str) -> bool:
    """
    Validate if a file is a valid PDF
    """
    try:
        if not file_path.lower().endswith('.pdf'):
            return False
        
        if not os.path.exists(file_path):
            return False
        
        # Try to open and read the PDF
        reader = PdfReader(file_path)
        if len(reader.pages) == 0:
            return False
        
        return True
        
    except Exception:
        return False

def get_pdf_info(file_path: str) -> dict:
    """
    Get basic information about a PDF file
    """
    try:
        reader = PdfReader(file_path)
        
        info = {
            "pages": len(reader.pages),
            "file_size": os.path.getsize(file_path),
            "filename": os.path.basename(file_path)
        }
        
        # Try to get metadata
        if reader.metadata:
            info["title"] = reader.metadata.get('/Title', 'Unknown')
            info["author"] = reader.metadata.get('/Author', 'Unknown')
            info["creator"] = reader.metadata.get('/Creator', 'Unknown')
        
        return info
        
    except Exception as e:
        logger.error(f"Error getting PDF info: {e}")
        return {"error": str(e)}
