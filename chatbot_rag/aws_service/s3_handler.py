#aws_service/s3_handler.py
import boto3
import os
import logging
from typing import Optional
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

# Initialize S3 client
try:
    s3 = boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        endpoint_url=os.getenv("ENDPOINT_URL", "http://localhost:4566")  # Use LocalStack for local development
    )
    logger.info("S3 client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize S3 client: {e}")
    s3 = None

def upload_pdf_to_s3(file_content: bytes, filename: str, bucket_name: str) -> Optional[str]:
    """
    Upload a PDF file to S3 bucket
    """
    if s3 is None:
        logger.error("S3 client not available")
        return None
    
    try:
        # Check if bucket exists, create if not
        try:
            s3.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.info(f"Creating bucket: {bucket_name}")
                s3.create_bucket(Bucket=bucket_name)
            else:
                raise
        
        # Upload file
        s3.put_object(
            Bucket=bucket_name, 
            Key=filename, 
            Body=file_content,
            ContentType='application/pdf'
        )
        
        # Generate URL
        if os.getenv("ENDPOINT_URL"):  # LocalStack
            url = f"{os.getenv('ENDPOINT_URL')}/{bucket_name}/{filename}"
        else:  # AWS S3
            url = f"https://{bucket_name}.s3.amazonaws.com/{filename}"
        
        logger.info(f"Successfully uploaded {filename} to S3")
        return url
        
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        return None
    except ClientError as e:
        logger.error(f"Error uploading to S3: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error uploading to S3: {e}")
        return None

def download_pdf_from_s3(filename: str, bucket_name: str, local_path: str) -> bool:
    """
    Download a PDF file from S3 bucket
    """
    if s3 is None:
        logger.error("S3 client not available")
        return False
    
    try:
        s3.download_file(bucket_name, filename, local_path)
        logger.info(f"Successfully downloaded {filename} from S3")
        return True
        
    except ClientError as e:
        logger.error(f"Error downloading from S3: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading from S3: {e}")
        return False

def delete_pdf_from_s3(filename: str, bucket_name: str) -> bool:
    """
    Delete a PDF file from S3 bucket
    """
    if s3 is None:
        logger.error("S3 client not available")
        return False
    
    try:
        s3.delete_object(Bucket=bucket_name, Key=filename)
        logger.info(f"Successfully deleted {filename} from S3")
        return True
        
    except ClientError as e:
        logger.error(f"Error deleting from S3: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deleting from S3: {e}")
        return False

def list_pdfs_in_s3(bucket_name: str) -> list:
    """
    List all PDF files in S3 bucket
    """
    if s3 is None:
        logger.error("S3 client not available")
        return []
    
    try:
        response = s3.list_objects_v2(Bucket=bucket_name)
        pdf_files = []
        
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'].lower().endswith('.pdf'):
                    pdf_files.append({
                        'filename': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat()
                    })
        
        logger.info(f"Found {len(pdf_files)} PDF files in S3 bucket")
        return pdf_files
        
    except ClientError as e:
        logger.error(f"Error listing S3 objects: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error listing S3 objects: {e}")
        return []

def check_s3_connection() -> bool:
    """
    Check if S3 connection is working
    """
    if s3 is None:
        return False
    
    try:
        s3.list_buckets()
        return True
    except Exception as e:
        logger.error(f"S3 connection check failed: {e}")
        return False
