#metrics_lambda/lambda_function.py
import json
import boto3
import os
from datetime import datetime

def lambda_handler(event, context):
    try:
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=os.getenv("ENDPOINT_URL", "http://localhost:4566"),
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        )
        table = dynamodb.Table("LLMMetrics")
        item = {
            "query_id": event.get("query_id", str(datetime.utcnow().timestamp())),
            "timestamp": datetime.utcnow().isoformat(),
            "query": event.get("query", ""),
            "response_time": str(event.get("response_time", "")),
            "response": event.get("response", "")[:1000]
        }
        table.put_item(Item=item)
        return {"status": "success", "item": item}
    except Exception as e:
        return {"status": "error", "message": str(e)}
