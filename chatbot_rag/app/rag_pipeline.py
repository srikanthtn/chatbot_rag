#app/rag_pipeline.py
import os
import logging
from dotenv import load_dotenv
from typing import List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.schema import Document
from langchain.memory import ConversationBufferMemory

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for required environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# --- TEXT SPLITTING ---
def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into chunks for better processing
    """
    if not text.strip():
        raise ValueError("Text cannot be empty")
    
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_text(text)
        logger.info(f"Text split into {len(chunks)} chunks")
        return chunks
    except Exception as e:
        logger.error(f"Error splitting text: {e}")
        raise

# --- VECTOR STORE CREATION ---
def get_vectorstore(text: str, persist_dir: str = "vectorstore") -> Chroma:
    """
    Create and return a vector store from text
    """
    try:
        # Split text into chunks
        chunks = split_text(text)
        
        # Create embeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            task_type="retrieval_document"
        )
        
        # Create vector store
        vectordb = Chroma.from_texts(
            texts=chunks,
            embedding=embeddings,
            persist_directory=persist_dir
        )
        
        # Note: Chroma 0.4.x automatically persists, no need for manual persist()
        logger.info(f"Vector store created and persisted to {persist_dir}")
        
        return vectordb
        
    except Exception as e:
        logger.error(f"Error creating vector store: {e}")
        raise

# --- QA CHAIN SETUP ---
def get_qa_chain(
    vectordb: Chroma, 
    model_name: str = "gemini-1.5-flash-8b", 
    temperature: float = 0.0,
    k: int = 4
) -> RetrievalQA:
    """
    Create and return a QA chain for question answering
    """
    try:
        # Configure retriever
        retriever = vectordb.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
        
        # Configure LLM
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            max_output_tokens=2048,
            safety_settings={
                1: 2,  # HARM_CATEGORY_HARASSMENT: BLOCK_MEDIUM_AND_ABOVE
                2: 2   # HARM_CATEGORY_HATE_SPEECH: BLOCK_MEDIUM_AND_ABOVE
            }
        )

        # Create QA chain
        chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            return_source_documents=True,
            chain_type="stuff",
            chain_type_kwargs={
                "prompt": None,  # Use default prompt
                "document_variable_name": "context"
            }
        )
        
        logger.info(f"QA chain created with model: {model_name}")
        return chain
        
    except Exception as e:
        logger.error(f"Error creating QA chain: {e}")
        raise

# --- MAIN RAG PIPELINE ---
def run_rag_pipeline(file_path: str, persist_dir: str = "vectorstore") -> RetrievalQA:
    """
    Complete RAG pipeline: extract text, create vector store, and return QA chain
    """
    try:
        from app.utils import extract_text_from_pdf
        
        # Extract text from PDF
        text = extract_text_from_pdf(file_path)
        if not text.strip():
            raise ValueError("No text extracted from PDF.")
        
        logger.info(f"Extracted {len(text)} characters from PDF")
        
        # Create vector store
        vectordb = get_vectorstore(text, persist_dir=persist_dir)
        
        # Create QA chain
        qa_chain = get_qa_chain(vectordb)
        
        return qa_chain
        
    except Exception as e:
        logger.error(f"Error in RAG pipeline: {e}")
        raise

# --- UTILITY FUNCTIONS ---
def clear_vectorstore(persist_dir: str = "vectorstore") -> None:
    """
    Clear the vector store directory
    """
    try:
        import shutil
        if os.path.exists(persist_dir):
            shutil.rmtree(persist_dir)
            logger.info(f"Cleared vector store: {persist_dir}")
    except Exception as e:
        logger.error(f"Error clearing vector store: {e}")
        raise

def get_vectorstore_info(persist_dir: str = "vectorstore") -> dict:
    """
    Get information about the current vector store
    """
    try:
        if not os.path.exists(persist_dir):
            return {"exists": False, "count": 0}
        
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vectordb = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
        
        collection = vectordb._collection
        count = collection.count()
        
        return {
            "exists": True,
            "count": count,
            "directory": persist_dir
        }
    except Exception as e:
        logger.error(f"Error getting vector store info: {e}")
        return {"exists": False, "error": str(e)}
