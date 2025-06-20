#!/usr/bin/env python3
"""
Initialize LocalStack services for RAG Chatbot
"""
import boto3
import time
import config

def wait_for_localstack():
    """Wait for LocalStack to be ready"""
    print("Waiting for LocalStack to be ready...")
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            # Test S3 connection
            s3 = boto3.client(
                's3',
                endpoint_url=config.ENDPOINT_URL,
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_REGION
            )
            s3.list_buckets()
            print("✅ LocalStack S3 is ready!")
            
            # Test DynamoDB connection
            dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=config.ENDPOINT_URL,
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_REGION
            )
            dynamodb.meta.client.list_tables()
            print("✅ LocalStack DynamoDB is ready!")
            return True
            
        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"⏳ Attempt {attempt + 1}/{max_attempts}: Waiting for LocalStack... ({e})")
                time.sleep(2)
            else:
                print(f"❌ LocalStack not ready after {max_attempts} attempts")
                return False

def create_s3_bucket():
    """Create S3 bucket for PDF storage"""
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=config.ENDPOINT_URL,
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION
        )
        
        # Check if bucket exists
        try:
            s3.head_bucket(Bucket=config.S3_BUCKET_NAME)
            print(f"✅ S3 bucket '{config.S3_BUCKET_NAME}' already exists")
        except:
            # Create bucket
            s3.create_bucket(Bucket=config.S3_BUCKET_NAME)
            print(f"✅ Created S3 bucket '{config.S3_BUCKET_NAME}'")
            
    except Exception as e:
        print(f"❌ Error creating S3 bucket: {e}")

def create_dynamodb_tables():
    """Create DynamoDB tables"""
    try:
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=config.ENDPOINT_URL,
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION
        )
        
        # Create PDF_Metadata table
        try:
            pdf_table = dynamodb.create_table(
                TableName='PDF_Metadata',
                KeySchema=[
                    {'AttributeName': 'filename', 'KeyType': 'HASH'},
                    {'AttributeName': 'user_id', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'filename', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            print("✅ Created PDF_Metadata table")
        except Exception as e:
            if "Table already exists" in str(e):
                print("✅ PDF_Metadata table already exists")
            else:
                print(f"❌ Error creating PDF_Metadata table: {e}")
        
        # Create LLMMetrics table
        try:
            metrics_table = dynamodb.create_table(
                TableName='LLMMetrics',
                KeySchema=[
                    {'AttributeName': 'query_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'query_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            print("✅ Created LLMMetrics table")
        except Exception as e:
            if "Table already exists" in str(e):
                print("✅ LLMMetrics table already exists")
            else:
                print(f"❌ Error creating LLMMetrics table: {e}")
                
    except Exception as e:
        print(f"❌ Error creating DynamoDB tables: {e}")

def main():
    """Main initialization function"""
    print("🚀 Initializing LocalStack services for RAG Chatbot...")
    print(f"📍 LocalStack endpoint: {config.ENDPOINT_URL}")
    
    # Wait for LocalStack to be ready
    if not wait_for_localstack():
        print("❌ Failed to connect to LocalStack. Make sure it's running.")
        return
    
    # Create S3 bucket
    create_s3_bucket()
    
    # Create DynamoDB tables
    create_dynamodb_tables()
    
    print("\n🎉 LocalStack initialization complete!")
    print("You can now run: uvicorn app.main:app --reload")

if __name__ == "__main__":
    main() 