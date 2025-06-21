import pytest
import os
import tempfile
import shutil
import sys
from unittest.mock import Mock, patch

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def test_data_dir():
    """Directory containing test data"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


@pytest.fixture(scope="session")
def sample_pdf_path(test_data_dir):
    """Path to sample PDF for testing"""
    pdf_path = os.path.join(test_data_dir, "Machine learning.pdf")
    if os.path.exists(pdf_path):
        return pdf_path
    else:
        pytest.skip("Sample PDF not found")


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_google_api_key():
    """Mock Google API key for testing"""
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key"}):
        yield "test_api_key"


@pytest.fixture
def mock_embeddings():
    """Mock embeddings for testing"""
    with patch('app.rag_pipeline.GoogleGenerativeAIEmbeddings') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_llm():
    """Mock LLM for testing"""
    with patch('app.rag_pipeline.ChatGoogleGenerativeAI') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_chroma():
    """Mock Chroma vector store for testing"""
    with patch('app.rag_pipeline.Chroma') as mock:
        mock_instance = Mock()
        mock.from_texts.return_value = mock_instance
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_text():
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
def mock_pdf_reader():
    """Mock PDF reader for testing"""
    with patch('app.utils.PdfReader') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture(autouse=True)
def setup_logging():
    """Setup logging for tests"""
    import logging
    logging.basicConfig(level=logging.INFO)


@pytest.fixture(autouse=True)
def setup_environment():
    """Setup environment variables for tests"""
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key"}):
        yield 