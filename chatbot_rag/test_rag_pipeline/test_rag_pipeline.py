import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
import sys

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag_pipeline import (
    split_text,
    get_vectorstore,
    get_qa_chain,
    run_rag_pipeline,
    clear_vectorstore,
    get_vectorstore_info
)
from app.utils import extract_text_from_pdf, validate_pdf_file, get_pdf_info


class TestRAGPipeline:
    """Test class for RAG pipeline functionality"""
    
    @pytest.fixture
    def sample_text(self):
        """Sample text for testing"""
        return """
        Machine learning is a subset of artificial intelligence that focuses on the development 
        of computer programs that can access data and use it to learn for themselves. 
        The process of learning begins with observations or data, such as examples, direct 
        experience, or instruction, in order to look for patterns in data and make better 
        decisions in the future based on the examples that we provide.
        
        There are three main types of machine learning: supervised learning, unsupervised 
        learning, and reinforcement learning. Supervised learning involves training a model 
        on labeled data, while unsupervised learning finds patterns in unlabeled data. 
        Reinforcement learning uses rewards and punishments to train models.
        """
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_embeddings(self):
        """Mock embeddings for testing"""
        with patch('app.rag_pipeline.GoogleGenerativeAIEmbeddings') as mock:
            mock_instance = Mock()
            mock.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for testing"""
        with patch('app.rag_pipeline.ChatGoogleGenerativeAI') as mock:
            mock_instance = Mock()
            mock.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def mock_chroma(self):
        """Mock Chroma vector store for testing"""
        with patch('app.rag_pipeline.Chroma') as mock:
            mock_instance = Mock()
            mock.from_texts.return_value = mock_instance
            mock.return_value = mock_instance
            yield mock_instance
    
    def test_split_text_success(self, sample_text):
        """Test successful text splitting"""
        chunks = split_text(sample_text, chunk_size=100, chunk_overlap=20)
        assert len(chunks) > 1
        assert all(len(chunk) <= 100 for chunk in chunks)
    
    def test_split_text_empty(self):
        """Test text splitting with empty text"""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            split_text("")
    
    def test_split_text_whitespace_only(self):
        """Test text splitting with whitespace only"""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            split_text("   \n\t   ")
    
    @patch('app.rag_pipeline.GoogleGenerativeAIEmbeddings')
    @patch('app.rag_pipeline.Chroma')
    def test_get_vectorstore_success(self, mock_chroma, mock_embeddings, sample_text, temp_dir):
        """Test successful vector store creation"""
        mock_embeddings_instance = Mock()
        mock_embeddings.return_value = mock_embeddings_instance
        
        mock_chroma_instance = Mock()
        mock_chroma.from_texts.return_value = mock_chroma_instance
        
        result = get_vectorstore(sample_text, persist_dir=temp_dir)
        
        assert result == mock_chroma_instance
        mock_chroma.from_texts.assert_called_once()
    
    @patch('app.rag_pipeline.GoogleGenerativeAIEmbeddings')
    @patch('app.rag_pipeline.ChatGoogleGenerativeAI')
    @patch('app.rag_pipeline.Chroma')
    def test_get_qa_chain_success(self, mock_chroma, mock_llm, mock_embeddings, temp_dir):
        """Test successful QA chain creation"""
        mock_vectordb = Mock()
        mock_retriever = Mock()
        mock_vectordb.as_retriever.return_value = mock_retriever
        
        mock_llm_instance = Mock()
        mock_llm.return_value = mock_llm_instance
        
        with patch('app.rag_pipeline.RetrievalQA') as mock_qa:
            mock_qa_instance = Mock()
            mock_qa.from_chain_type.return_value = mock_qa_instance
            
            result = get_qa_chain(mock_vectordb)
            
            assert result == mock_qa_instance
            mock_qa.from_chain_type.assert_called_once()
    
    @patch('app.utils.extract_text_from_pdf')
    @patch('app.rag_pipeline.get_vectorstore')
    @patch('app.rag_pipeline.get_qa_chain')
    def test_run_rag_pipeline_success(self, mock_get_qa, mock_get_vectorstore, mock_extract_text, temp_dir):
        """Test successful RAG pipeline execution"""
        mock_text = "Sample extracted text"
        mock_extract_text.return_value = mock_text
        
        mock_vectordb = Mock()
        mock_get_vectorstore.return_value = mock_vectordb
        
        mock_qa_chain = Mock()
        mock_get_qa.return_value = mock_qa_chain
        
        result = run_rag_pipeline("test.pdf", persist_dir=temp_dir)
        
        assert result == mock_qa_chain
        mock_extract_text.assert_called_once_with("test.pdf")
        mock_get_vectorstore.assert_called_once_with(mock_text, persist_dir=temp_dir)
        mock_get_qa.assert_called_once_with(mock_vectordb)
    
    @patch('app.utils.extract_text_from_pdf')
    def test_run_rag_pipeline_no_text_extracted(self, mock_extract_text):
        """Test RAG pipeline with no text extracted"""
        mock_extract_text.return_value = ""
        
        with pytest.raises(ValueError, match="No text extracted from PDF"):
            run_rag_pipeline("test.pdf")
    
    def test_clear_vectorstore_success(self, temp_dir):
        """Test successful vector store clearing"""
        # Create a dummy file in temp_dir
        with open(os.path.join(temp_dir, "test.txt"), "w") as f:
            f.write("test")
        
        clear_vectorstore(temp_dir)
        assert not os.path.exists(temp_dir)
    
    def test_clear_vectorstore_nonexistent(self):
        """Test clearing non-existent vector store"""
        # Should not raise an error
        clear_vectorstore("nonexistent_dir")
    
    @patch('app.rag_pipeline.GoogleGenerativeAIEmbeddings')
    @patch('app.rag_pipeline.Chroma')
    def test_get_vectorstore_info_exists(self, mock_chroma, mock_embeddings, temp_dir):
        """Test getting vector store info when it exists"""
        # Create temp_dir to simulate existing vector store
        os.makedirs(temp_dir, exist_ok=True)
        
        mock_embeddings_instance = Mock()
        mock_embeddings.return_value = mock_embeddings_instance
        
        mock_chroma_instance = Mock()
        mock_collection = Mock()
        mock_collection.count.return_value = 10
        mock_chroma_instance._collection = mock_collection
        mock_chroma.return_value = mock_chroma_instance
        
        result = get_vectorstore_info(temp_dir)
        
        assert result["exists"] is True
        assert result["count"] == 10
        assert result["directory"] == temp_dir
    
    def test_get_vectorstore_info_nonexistent(self):
        """Test getting vector store info when it doesn't exist"""
        result = get_vectorstore_info("nonexistent_dir")
        assert result["exists"] is False
        assert result["count"] == 0


class TestPDFUpload:
    """Test class for PDF upload and processing functionality"""
    
    @pytest.fixture
    def sample_pdf_path(self):
        """Path to sample PDF for testing"""
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Machine learning.pdf")
    
    @pytest.fixture
    def temp_pdf_path(self):
        """Create a temporary PDF file for testing"""
        temp_dir = tempfile.mkdtemp()
        temp_pdf = os.path.join(temp_dir, "test.pdf")
        
        # Create a simple PDF-like file for testing
        with open(temp_pdf, "wb") as f:
            f.write(b"%PDF-1.4\n%Test PDF content\n%%EOF")
        
        yield temp_pdf
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_extract_text_from_pdf_success(self, sample_pdf_path):
        """Test successful PDF text extraction with real PDF"""
        if os.path.exists(sample_pdf_path):
            text = extract_text_from_pdf(sample_pdf_path)
            assert isinstance(text, str)
            assert len(text) > 0
            assert "machine learning" in text.lower() or "artificial intelligence" in text.lower()
        else:
            pytest.skip("Sample PDF not found")
    
    def test_extract_text_from_pdf_file_not_found(self):
        """Test PDF text extraction with non-existent file"""
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            extract_text_from_pdf("nonexistent.pdf")
    
    def test_extract_text_from_pdf_empty_file(self, temp_dir):
        """Test PDF text extraction with empty file"""
        empty_pdf = os.path.join(temp_dir, "empty.pdf")
        with open(empty_pdf, "wb") as f:
            f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n%%EOF")
        
        with pytest.raises(ValueError, match="PDF file is empty or corrupted"):
            extract_text_from_pdf(empty_pdf)
    
    def test_validate_pdf_file_valid(self, sample_pdf_path):
        """Test PDF validation with valid file"""
        if os.path.exists(sample_pdf_path):
            assert validate_pdf_file(sample_pdf_path) is True
        else:
            pytest.skip("Sample PDF not found")
    
    def test_validate_pdf_file_invalid_extension(self):
        """Test PDF validation with invalid file extension"""
        assert validate_pdf_file("test.txt") is False
    
    def test_validate_pdf_file_nonexistent(self):
        """Test PDF validation with non-existent file"""
        assert validate_pdf_file("nonexistent.pdf") is False
    
    def test_get_pdf_info_success(self, sample_pdf_path):
        """Test getting PDF information"""
        if os.path.exists(sample_pdf_path):
            info = get_pdf_info(sample_pdf_path)
            assert "pages" in info
            assert "file_size" in info
            assert "filename" in info
            assert info["pages"] > 0
            assert info["file_size"] > 0
        else:
            pytest.skip("Sample PDF not found")
    
    def test_get_pdf_info_error(self):
        """Test getting PDF info with invalid file"""
        info = get_pdf_info("nonexistent.pdf")
        assert "error" in info


class TestIntegration:
    """Integration tests for complete RAG pipeline with PDF upload"""
    
    @pytest.fixture
    def sample_pdf_path(self):
        """Path to sample PDF for testing"""
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Machine learning.pdf")
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @patch('app.rag_pipeline.GoogleGenerativeAIEmbeddings')
    @patch('app.rag_pipeline.ChatGoogleGenerativeAI')
    @patch('app.rag_pipeline.Chroma')
    def test_complete_rag_pipeline_with_pdf(self, mock_chroma, mock_llm, mock_embeddings, sample_pdf_path, temp_dir):
        """Test complete RAG pipeline with PDF upload"""
        if not os.path.exists(sample_pdf_path):
            pytest.skip("Sample PDF not found")
        
        # Mock all external dependencies
        mock_embeddings_instance = Mock()
        mock_embeddings.return_value = mock_embeddings_instance
        
        mock_chroma_instance = Mock()
        mock_retriever = Mock()
        mock_chroma_instance.as_retriever.return_value = mock_retriever
        mock_chroma.from_texts.return_value = mock_chroma_instance
        mock_chroma.return_value = mock_chroma_instance
        
        mock_llm_instance = Mock()
        mock_llm.return_value = mock_llm_instance
        
        with patch('app.rag_pipeline.RetrievalQA') as mock_qa:
            mock_qa_instance = Mock()
            mock_qa.from_chain_type.return_value = mock_qa_instance
            
            # Run the complete pipeline
            result = run_rag_pipeline(sample_pdf_path, persist_dir=temp_dir)
            
            # Verify the result
            assert result == mock_qa_instance
            
            # Verify that all components were called
            mock_chroma.from_texts.assert_called_once()
            mock_qa.from_chain_type.assert_called_once()
    
    def test_pdf_upload_workflow(self, sample_pdf_path, temp_dir):
        """Test complete PDF upload workflow"""
        if not os.path.exists(sample_pdf_path):
            pytest.skip("Sample PDF not found")
        
        # Step 1: Validate PDF
        assert validate_pdf_file(sample_pdf_path) is True
        
        # Step 2: Get PDF info
        info = get_pdf_info(sample_pdf_path)
        assert info["pages"] > 0
        assert info["file_size"] > 0
        
        # Step 3: Extract text
        text = extract_text_from_pdf(sample_pdf_path)
        assert len(text) > 0
        
        # Step 4: Split text
        chunks = split_text(text, chunk_size=1000, chunk_overlap=200)
        assert len(chunks) > 0
        
        # Step 5: Test vector store info (without creating actual vector store)
        info = get_vectorstore_info(temp_dir)
        # The temp_dir might exist, so we just check the structure
        assert "exists" in info
        assert "count" in info


if __name__ == "__main__":
    pytest.main([__file__]) 