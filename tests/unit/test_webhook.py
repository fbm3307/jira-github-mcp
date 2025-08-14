"""Simple webhook server for testing without Jira dependency."""

import asyncio
import logging
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI(title="Test Webhook Server")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    return {"message": "Test webhook server is running!"}

@app.post("/webhook")
async def webhook_handler(request: Request):
    """Test webhook endpoint."""
    body = await request.body()
    headers = dict(request.headers)
    
    logger.info(f"Received webhook: {len(body)} bytes")
    logger.info(f"Headers: {headers}")
    
    return {"status": "received", "message": "Webhook test successful"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    logger.info("Starting test webhook server on port 3000...")
    uvicorn.run(app, host="0.0.0.0", port=3000) 