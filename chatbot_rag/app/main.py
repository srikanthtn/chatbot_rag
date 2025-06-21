#app/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import os
import logging
from typing import Optional
import time
from tenacity import retry, stop_after_attempt, wait_fixed
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.utils import extract_text_from_pdf
from app.rag_pipeline import get_vectorstore, get_qa_chain, clear_vectorstore
import config

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Chatbot API", description="Upload PDF and ask questions")

# Global variables
qa_chain = None
current_pdf_name = None

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
DATA_DIR = "data"
UPLOADS_DIR = "uploads"
Path(DATA_DIR).mkdir(exist_ok=True)
Path(UPLOADS_DIR).mkdir(exist_ok=True)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if config.AWS_AVAILABLE:
    try:
        from aws_service.dynamo_handler import setup_tables
        setup_tables()
    except Exception as e:
        logger.warning(f"Failed to setup DynamoDB tables: {e}")

@app.post("/upload-pdf/")
@limiter.limit("5/minute")  # 5 requests per minute per IP
async def upload_pdf(request: Request, file: UploadFile = File(...)):
    """
    Upload and process a PDF file for RAG-based question answering
    """
    global qa_chain, current_pdf_name
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        if file.size and file.size > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(status_code=400, detail="File size too large. Maximum 50MB allowed")

        logger.info(f"Processing PDF: {file.filename}")
        
        # Save file locally
        file_path = os.path.join(DATA_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract text from PDF
        text = extract_text_from_pdf(file_path)
        if not text.strip():
            os.remove(file_path)
            raise HTTPException(
                status_code=400, 
                detail="No text found in PDF. It may be scanned, empty, or corrupted."
            )

        # Optional AWS integration
        if config.AWS_AVAILABLE:
            try:
                from aws_service.s3_handler import upload_pdf_to_s3
                from aws_service.dynamo_handler import store_metadata
                
                # Upload to S3
                with open(file_path, "rb") as f:
                    file_content = f.read()
                s3_url = upload_pdf_to_s3(file_content, file.filename, config.S3_BUCKET_NAME)
                if s3_url:
                    logger.info(f"PDF uploaded to S3: {s3_url}")
                
                # Store metadata
                user_id_value = 'anonymous'
                if store_metadata(file.filename, user_id=user_id_value):
                    logger.info(f"Metadata stored for: {file.filename}")
                    
            except Exception as e:
                logger.warning(f"AWS integration failed: {e}")
        else:
            logger.info("AWS services not configured, skipping S3 upload and metadata storage")

        # Create vector store and QA chain
        vectordb = get_vectorstore(text)
        qa_chain = get_qa_chain(vectordb)
        current_pdf_name = file.filename

        # Get list of available PDFs
        pdf_files = []
        if os.path.exists(DATA_DIR):
            pdf_files = [
                f for f in os.listdir(DATA_DIR) 
                if f.lower().endswith('.pdf') and os.path.isfile(os.path.join(DATA_DIR, f))
            ]

        return JSONResponse({
            "message": f"PDF '{file.filename}' processed successfully",
            "filename": file.filename,
            "text_length": len(text),
            "available_pdfs": sorted(pdf_files),
            "status": "ready_for_questions"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/ask")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def ask_question(request: Request, question: str = Form(...)):
    """
    Ask a question about the uploaded PDF
    """
    global qa_chain, current_pdf_name
    
    if qa_chain is None:
        raise HTTPException(
            status_code=400, 
            detail="No PDF uploaded. Please upload a PDF first using /upload-pdf/"
        )

    if not question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        start_time = time.time()
        
        # Get answer from RAG chain
        response = qa_chain.invoke({"query": question})
        answer = response["result"]
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Optional AWS metrics storage
        if config.AWS_AVAILABLE:
            try:
                from aws_service.dynamo_handler import store_llm_metrics
                @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
                def store_llm_metrics_retry(question, response_time, answer, pdf_name):
                    store_llm_metrics(question, response_time, answer, pdf_name)
                store_llm_metrics_retry(question, response_time, answer, current_pdf_name)
            except Exception as e:
                logger.warning(f"Failed to store metrics: {e}")

        return JSONResponse({
            "answer": answer,
            "question": question,
            "pdf_name": current_pdf_name,
            "response_time": round(response_time, 2),
            "sources": [doc.page_content[:200] + "..." for doc in response.get("source_documents", [])]
        })

    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@app.get("/status")
async def get_status():
    """
    Get current status of the RAG system
    """
    global qa_chain, current_pdf_name
    
    return JSONResponse({
        "pdf_loaded": qa_chain is not None,
        "current_pdf": current_pdf_name,
        "status": "ready" if qa_chain else "no_pdf_loaded"
    })


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return JSONResponse({"status": "healthy", "service": "RAG Chatbot API"})


@app.post("/clear-vectorstore/")
def clear_vectorstore_endpoint():
    try:
        clear_vectorstore("vectorstore")
        return {"status": "success", "message": "Vector store cleared."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
