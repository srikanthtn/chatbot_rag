# Configuration file for RAG Chatbot
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google AI Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("WARNING: GOOGLE_API_KEY not set. Please set it in your .env file")

# AWS Configuration (LocalStack for local development)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
ENDPOINT_URL = os.getenv("ENDPOINT_URL", "http://localhost:4566")

# S3 Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "pdf-storage-bucket")

# Application Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "52428800"))  # 50MB in bytes

# Check if AWS services are available
AWS_AVAILABLE = True

# print(f"Using LocalStack endpoint: {ENDPOINT_URL}")
# print(f"S3 Bucket: {S3_BUCKET_NAME}")
# print(f"AWS Region: {AWS_REGION}")
# print("AWS services enabled for LocalStack") 