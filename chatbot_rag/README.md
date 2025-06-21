# RAG Chatbot with LocalStack Integration

This project is a Retrieval-Augmented Generation (RAG) chatbot that allows you to upload PDFs, ask questions, and stores related data in AWS services (S3, DynamoDB) via LocalStack. It also supports storing LLM metrics via a Lambda function.

---

## Prerequisites
- **Python 3.10+**
- **Docker Desktop** (for LocalStack)
- **Node.js** (optional, for advanced frontend)
- **awslocal**: `pip install awscli-local`
- **AWS CLI**: `pip install awscli` (optional)

---

## 1. Clone and Install Dependencies
```sh
cd chatbot_rag
pip install -r requirements.txt
```

### **Updated Dependencies**
The project now uses:
- **pypdf** (replaces deprecated PyPDF2) for PDF processing
- **pytest** for testing framework
- **pytest-cov** for test coverage
- **pytest-mock** for mocking in tests

---

## 2. Testing

### **Run All Tests**
```sh
# From the chatbot_rag directory
pytest test_rag_pipeline/ -v
```

### **Run Specific Test Files**
```sh
# Test PDF upload functionality
pytest test_rag_pipeline/test_pdf_upload.py -v

# Test RAG pipeline functionality
pytest test_rag_pipeline/test_rag_pipeline.py -v
```

### **Run Tests with Coverage**
```sh
pytest test_rag_pipeline/ --cov=app --cov-report=html
```

### **Test Structure**
```
test_rag_pipeline/
├── __init__.py                    # Package initialization
├── conftest.py                    # Pytest configuration and fixtures
├── test_rag_pipeline.py           # Main RAG pipeline tests
└── test_pdf_upload.py             # PDF upload specific tests
```

### **Test Coverage**
- **PDF Upload Tests**: File validation, text extraction, metadata retrieval
- **RAG Pipeline Tests**: Text splitting, vector store creation, QA chain setup
- **Integration Tests**: Complete workflow testing
- **Error Handling**: Various failure scenarios and edge cases

---

## 3. Start LocalStack (AWS Emulation)
```sh
docker run --rm -it -p 4566:4566 localstack/localstack
```
Wait for "Ready." in the logs.

---

## 4. Create S3 Bucket and DynamoDB Tables

### **Create S3 Bucket**
```sh
awslocal s3 mb s3://pdf-storage-bucket
```

### **Create DynamoDB Tables**
```sh
awslocal dynamodb create-table --table-name PDF_Metadata --attribute-definitions AttributeName=filename,AttributeType=S AttributeName=user_id,AttributeType=S --key-schema AttributeName=filename,KeyType=HASH AttributeName=user_id,KeyType=RANGE --billing-mode PAY_PER_REQUEST

awslocal dynamodb create-table --table-name LLMMetrics --attribute-definitions AttributeName=query_id,AttributeType=S AttributeName=timestamp,AttributeType=S --key-schema AttributeName=query_id,KeyType=HASH AttributeName=timestamp,KeyType=RANGE --billing-mode PAY_PER_REQUEST 
```

---

## 5. (Optional) Deploy Lambda for Metrics

### **Zip the Lambda Function (PowerShell):**
```powershell
Compress-Archive -Path .\metrics_lambda\lambda_function.py -DestinationPath function.zip -Force
```

### **Create or Update Lambda in LocalStack:**
```sh
awslocal lambda create-function \
  --function-name store-llm-metrics \
  --runtime python3.11 \
  --handler lambda_function.lambda_handler \
  --role arn:aws:iam::000000000000:role/lambda-role \
  --zip-file fileb://function.zip
# If function exists, update:
awslocal lambda update-function-code \
  --function-name store-llm-metrics \
  --zip-file fileb://function.zip
```

### **Test Lambda:**
```sh
awslocal lambda invoke \
  --function-name store-llm-metrics \
  --payload '{"query_id": "q1", "query": "What is ML?", "response_time": 1.2, "response": "ML is..."}' \
  output.json
```

---

## 6. Run the Backend (FastAPI)
```powershell
cd chatbot_rag
uvicorn app.main:app --reload --port 8000
```
- Visit [http://localhost:8000/docs](http://localhost:8000/docs) for API docs.

---

## 7. Run the Frontend (Static HTML/JS)
```powershell
cd chatbot_rag/frontend
python -m http.server 8080
```
- Visit [http://localhost:8080](http://localhost:8080)

---

## 8. Upload a PDF and Ask Questions

### **Upload PDF (curl):**
```sh
curl -X POST "http://localhost:8000/upload-pdf/" -F "file=@data/ml.pdf"
```

### **Ask a Question (curl):**
```sh
curl -X POST "http://localhost:8000/ask" -d "question=What is machine learning?"
```

---

## 9. Verify Data in S3 and DynamoDB

### **Check S3 Bucket:**
```sh
awslocal s3 ls s3://pdf-storage-bucket
```

### **Check PDF Metadata in DynamoDB:**
```sh
awslocal dynamodb scan --table-name PDF_Metadata
```

### **Check LLM Metrics in DynamoDB:**
```sh
awslocal dynamodb scan --table-name LLMMetrics
```

## **Clear Vector Store**
```sh
curl -X POST http://localhost:8000/clear-vectorstore/
```

---

## 10. Troubleshooting
- **ModuleNotFoundError: No module named 'app'**: Run `uvicorn` from inside the `chatbot_rag` directory.
- **Upload failed**: Check backend logs for errors, ensure S3 bucket and DynamoDB tables exist.
- **No data in DynamoDB**: Restart backend after creating tables, check logs for errors.
- **Lambda errors**: Make sure the table exists, check Lambda logs/output for error messages.
- **Test failures**: Ensure all dependencies are installed, check that sample PDF exists in data folder.
- **Credentials error**: Set these env vars in your terminal:
  ```powershell
  $env:AWS_ACCESS_KEY_ID="test"
  $env:AWS_SECRET_ACCESS_KEY="test"
  $env:AWS_REGION="us-east-1"
  ```

---

## 11. Example .env
```
ENDPOINT_URL=http://localhost:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_REGION=us-east-1
S3_BUCKET_NAME=pdf-storage-bucket
GOOGLE_API_KEY=your_google_api_key_here
```

---

## 12. Useful awslocal Commands
- List S3 buckets: `awslocal s3 ls`
- List DynamoDB tables: `awslocal dynamodb list-tables`
- Scan a table: `awslocal dynamodb scan --table-name PDF_Metadata`
- Put an item (PowerShell):
  ```powershell
  awslocal dynamodb put-item --table-name PDF_Metadata --item '{"filename": {"S": "test.pdf"}, "user_id": {"S": "testuser"}}'
  ```

---

## 13. Project Structure
```
chatbot_rag/
├── app/                          # Main application code
│   ├── main.py                   # FastAPI application
│   ├── rag_pipeline.py           # RAG pipeline implementation
│   └── utils.py                  # Utility functions (PDF processing)
├── test_rag_pipeline/            # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Pytest configuration
│   ├── test_rag_pipeline.py      # RAG pipeline tests
│   └── test_pdf_upload.py        # PDF upload tests
├── data/                         # Sample data
│   └── Machine learning.pdf      # Sample PDF for testing
├── aws_service/                  # AWS service handlers
├── metrics_lambda/               # Lambda function for metrics
├── frontend/                     # Static frontend files
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## 14. Notes
- Always restart your backend after creating new DynamoDB tables.
- For Lambda, always re-zip and update after code changes.
- Use [http://localhost:8000/docs](http://localhost:8000/docs) for API testing.
- Run tests before deploying to ensure code quality.
- The project now uses `pypdf` instead of the deprecated `PyPDF2`.

---

**You are now ready to run, test, and verify your full RAG + LocalStack stack!** 