import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils import extract_text_from_pdf, validate_pdf_file, get_pdf_info


def test_extract_text_from_pdf_success(sample_pdf_path):
    """Test PDF text extraction"""
    if os.path.exists(sample_pdf_path):
        text = extract_text_from_pdf(sample_pdf_path)
        assert isinstance(text, str)
        assert len(text) > 0
    else:
        pytest.skip("Sample PDF not found")


def test_extract_text_from_pdf_file_not_found():
    """Test PDF extraction with non-existent file"""
    with pytest.raises(FileNotFoundError):
        extract_text_from_pdf("nonexistent.pdf")


def test_validate_pdf_file_valid(sample_pdf_path):
    """Test PDF validation"""
    if os.path.exists(sample_pdf_path):
        assert validate_pdf_file(sample_pdf_path) is True
    else:
        pytest.skip("Sample PDF not found")


def test_validate_pdf_file_invalid():
    """Test PDF validation with invalid file"""
    assert validate_pdf_file("test.txt") is False
    assert validate_pdf_file("nonexistent.pdf") is False


def test_get_pdf_info_success(sample_pdf_path):
    """Test getting PDF info"""
    if os.path.exists(sample_pdf_path):
        info = get_pdf_info(sample_pdf_path)
        assert "pages" in info
        assert "file_size" in info
        assert info["pages"] > 0
    else:
        pytest.skip("Sample PDF not found")


def test_get_pdf_info_error():
    """Test getting PDF info with invalid file"""
    info = get_pdf_info("nonexistent.pdf")
    assert "error" in info


def test_pdf_upload_workflow(sample_pdf_path):
    """Test basic PDF upload workflow"""
    if not os.path.exists(sample_pdf_path):
        pytest.skip("Sample PDF not found")
    
    # Validate PDF
    assert validate_pdf_file(sample_pdf_path) is True
    
    # Get info
    info = get_pdf_info(sample_pdf_path)
    assert info["pages"] > 0
    
    # Extract text
    text = extract_text_from_pdf(sample_pdf_path)
    assert len(text) > 0 