import boto3
import os
import logging
from botocore.exceptions import ClientError
from datetime import datetime
import time
from typing import Optional, Dict, Any, Union
from boto3.resources.base import ServiceResource
from botocore.client import BaseClient

logger = logging.getLogger(__name__)

# Initialize DynamoDB client
dynamodb: Optional[ServiceResource] = None
dynamodb_client: Optional[BaseClient] = None

try:
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        endpoint_url=os.getenv("ENDPOINT_URL", "http://localhost:4566")
    )
    
    # Test connection
    if dynamodb:
        dynamodb_client = dynamodb.meta.client  # type: ignore
        tables = dynamodb_client.list_tables()  # type: ignore
        logger.info(f"Successfully connected to DynamoDB. Tables: {tables.get('TableNames', [])}")
    
except Exception as e:
    logger.error(f"Failed to connect to DynamoDB: {e}")
    dynamodb = None
    dynamodb_client = None

# Initialize table references
pdf_metadata_table = None
llm_metrics_table = None

def initialize_tables():
    """
    Initialize DynamoDB table references
    """
    global pdf_metadata_table, llm_metrics_table
    
    if dynamodb is None:
        logger.error("DynamoDB not available")
        return False
    
    try:
        pdf_metadata_table = dynamodb.Table("PDF_Metadata")  # type: ignore
        llm_metrics_table = dynamodb.Table("LLMMetrics")  # type: ignore
        logger.info("DynamoDB table references initialized")
        return True
    except Exception as e:
        logger.error(f"Error initializing table references: {e}")
        return False

def create_dynamodb_table(table_name: str, partition_key: str, sort_key: Optional[str] = None) -> bool:
    """
    Create a DynamoDB table if it doesn't exist
    """
    if dynamodb is None or dynamodb_client is None:
        logger.error("DynamoDB not available")
        return False
    
    try:
        key_schema = [
            {'AttributeName': partition_key, 'KeyType': 'HASH'}
        ]
        attribute_definitions = [
            {'AttributeName': partition_key, 'AttributeType': 'S'}
        ]
        
        if sort_key:
            key_schema.append({'AttributeName': sort_key, 'KeyType': 'RANGE'})
            attribute_definitions.append({'AttributeName': sort_key, 'AttributeType': 'S'})
        
        dynamodb_client.create_table(
            TableName=table_name,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_definitions,
            BillingMode='PAY_PER_REQUEST'
        )
        logger.info(f"Table '{table_name}' created successfully")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            logger.info(f"Table '{table_name}' already exists")
            return True
        else:
            logger.error(f"Error creating table '{table_name}': {e}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error creating table '{table_name}': {e}")
        return False

def setup_tables():
    """
    Setup required DynamoDB tables
    """
    success = True
    
    # Create PDF_Metadata table
    if not create_dynamodb_table(
        table_name='PDF_Metadata',
        partition_key='filename',
        sort_key='user_id'
    ):
        success = False
    
    # Create LLMMetrics table
    if not create_dynamodb_table(
        table_name='LLMMetrics',
        partition_key='query_id',
        sort_key='timestamp'
    ):
        success = False
    
    # Initialize table references
    if success:
        initialize_tables()
    
    return success

def store_metadata(filename: str, user_id: str = "anonymous", additional_info: Optional[Dict[str, Any]] = None) -> bool:
    """
    Store PDF metadata in the PDF_Metadata table
    """
    if pdf_metadata_table is None:
        logger.error("PDF_Metadata table not available")
        return False
    
    try:
        item = {
            'filename': filename,
            'user_id': user_id,
            'upload_timestamp': datetime.utcnow().isoformat(),
            'status': 'processed'
        }
        
        if additional_info:
            item.update(additional_info)
        
        logger.debug(f"Storing item in DynamoDB: {item}")
        pdf_metadata_table.put_item(Item=item)
        logger.info(f"Stored metadata for filename: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing metadata: {e}")
        return False

def store_llm_metrics(query: str, response_time: float, response: str, pdf_name: Optional[str] = None) -> bool:
    """
    Store LLM metrics in the LLMMetrics table
    """
    if llm_metrics_table is None:
        logger.error("LLMMetrics table not available")
        return False
    
    try:
        query_id = f"query_{int(time.time() * 1000)}"
        item = {
            'query_id': query_id,
            'timestamp': datetime.utcnow().isoformat(),
            'query': query[:500],  # Limit query length
            'response_time': str(round(response_time, 3)),
            'response_length': len(response),
            'response_preview': response[:200] + "..." if len(response) > 200 else response
        }
        
        if pdf_name:
            item['pdf_name'] = pdf_name
        
        llm_metrics_table.put_item(Item=item)
        logger.info(f"Stored metrics for query_id: {query_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing LLM metrics: {e}")
        return False

def get_pdf_metadata(filename: str, user_id: str = "anonymous") -> Optional[Dict[str, Any]]:
    """
    Retrieve PDF metadata from DynamoDB
    """
    if pdf_metadata_table is None:
        logger.error("PDF_Metadata table not available")
        return None
    
    try:
        response = pdf_metadata_table.get_item(
            Key={
                'filename': filename,
                'user_id': user_id
            }
        )
        
        if 'Item' in response:
            return response['Item']
        else:
            logger.info(f"No metadata found for filename: {filename}")
            return None
            
    except Exception as e:
        logger.error(f"Error retrieving metadata: {e}")
        return None

def get_llm_metrics(query_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve LLM metrics from DynamoDB
    """
    if llm_metrics_table is None:
        logger.error("LLMMetrics table not available")
        return None
    
    try:
        response = llm_metrics_table.get_item(
            Key={
                'query_id': query_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        if 'Item' in response:
            return response['Item']
        else:
            logger.info(f"No metrics found for query_id: {query_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error retrieving metrics: {e}")
        return None

def list_user_pdfs(user_id: str = "anonymous") -> list:
    """
    List all PDFs for a specific user
    """
    if pdf_metadata_table is None:
        logger.error("PDF_Metadata table not available")
        return []
    
    try:
        response = pdf_metadata_table.query(
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        
        return response.get('Items', [])
        
    except Exception as e:
        logger.error(f"Error listing user PDFs: {e}")
        return []

def check_dynamodb_connection() -> bool:
    """
    Check if DynamoDB connection is working
    """
    if dynamodb is None or dynamodb_client is None:
        return False
    
    try:
        dynamodb_client.list_tables()
        return True
    except Exception as e:
        logger.error(f"DynamoDB connection check failed: {e}")
        return False

# Initialize tables when module is imported
if dynamodb is not None:
    initialize_tables()