# #aws_service/app.py
# from fastapi import FastAPI, UploadFile, File
# from s3_handler import upload_pdf_to_s3
# from dynamo_handler import store_metadata
# from rag_model_service.rag_pipeline import run_rag_pipeline  # adjust import if needed
# import sys, os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# app = FastAPI()

# BUCKET_NAME = "pdf-storage-bucket"

# @app.post("/upload/")
# async def upload_file(file: UploadFile = File(...)):
#     content = await file.read()
#     upload_pdf_to_s3(content, file.filename, BUCKET_NAME)
#     store_metadata(file.filename)
    
#     # Call RAG Pipeline
#     run_rag_pipeline(file.filename)
    
#     return {"status": "success", "filename": file.filename}
