import os
import time
import logging
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
from tools.server.fastapi_app import app

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handler(event):
    """
    RunPod serverless handler function
    """
    try:
        # Convert RunPod event to ASGI scope
        scope = {
            "type": "http",
            "method": event["httpMethod"],
            "path": event["path"],
            "headers": [
                (key.encode(), value.encode())
                for key, value in event.get("headers", {}).items()
            ],
            "query_string": event.get("queryStringParameters", "").encode(),
        }

        # Create ASGI receive function
        async def receive():
            return {
                "type": "http.request",
                "body": event.get("body", b""),
                "more_body": False
            }

        # Create ASGI send function
        response = {
            "statusCode": 500,
            "headers": {},
            "body": ""
        }

        async def send(message):
            if message["type"] == "http.response.start":
                response["statusCode"] = message["status"]
                response["headers"] = {
                    key.decode(): value.decode()
                    for key, value in message.get("headers", [])
                }
            elif message["type"] == "http.response.body":
                response["body"] = message.get("body", b"").decode()

        # Call the FastAPI app
        await app(scope, receive, send)

        return response

    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

def run_server():
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        timeout_keep_alive=300,
    )

if __name__ == "__main__":
    run_server()