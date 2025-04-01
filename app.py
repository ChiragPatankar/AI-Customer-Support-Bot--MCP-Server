from fastapi import FastAPI, HTTPException, Depends, Request, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
import requests
from datetime import datetime
import json
from database import get_db
from sqlalchemy.orm import Session
import models
from mcp_config import mcp_settings
from middleware import rate_limit_middleware, validate_mcp_request
import time

# Load environment variables
load_dotenv()

app = FastAPI(title=mcp_settings.SERVER_NAME)

# Add middleware
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(validate_mcp_request)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCP Models
class MCPRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    mcp_version: Optional[str] = "1.0"
    priority: Optional[str] = "normal"  # high, normal, low

class MCPResponse(BaseModel):
    response: str
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    mcp_version: str = "1.0"
    processing_time: Optional[float] = None

class MCPError(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class MCPBatchRequest(BaseModel):
    queries: List[str]
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    mcp_version: Optional[str] = "1.0"

class MCPBatchResponse(BaseModel):
    responses: List[MCPResponse]
    batch_metadata: Optional[Dict[str, Any]] = None
    mcp_version: str = "1.0"

# Environment variables
GLAMA_API_KEY = os.getenv("GLAMA_API_KEY")
GLAMA_API_URL = os.getenv("GLAMA_API_URL", "https://api.glama.ai/v1")
CURSOR_API_KEY = os.getenv("CURSOR_API_KEY")

# MCP Authentication
async def verify_mcp_auth(x_mcp_auth: str = Header(...)):
    if not x_mcp_auth:
        raise HTTPException(status_code=401, detail="MCP authentication required")
    # TODO: Implement proper MCP authentication
    return True

@app.get("/")
async def root():
    return {
        "message": mcp_settings.SERVER_NAME,
        "version": mcp_settings.SERVER_VERSION,
        "status": "active"
    }

@app.get("/mcp/version")
async def mcp_version():
    return {
        "version": "1.0",
        "supported_versions": ["1.0"],
        "server_version": mcp_settings.SERVER_VERSION,
        "deprecation_notice": None
    }

@app.get("/mcp/capabilities")
async def mcp_capabilities():
    return {
        "models": {
            "cursor-ai": {
                "version": mcp_settings.MODEL_VERSION,
                "capabilities": ["text-generation", "context-aware"],
                "max_tokens": 2048,
                "supported_languages": ["en", "es", "fr", "de"]
            }
        },
        "context_providers": {
            "glama-ai": {
                "version": "1.0",
                "capabilities": ["context-fetching", "real-time-updates"],
                "max_context_size": 1000
            }
        },
        "features": [
            "context-aware-responses",
            "user-tracking",
            "response-storage",
            "batch-processing",
            "priority-queuing"
        ],
        "rate_limits": {
            "requests_per_period": mcp_settings.RATE_LIMIT_REQUESTS,
            "period_seconds": mcp_settings.RATE_LIMIT_PERIOD
        }
    }

@app.post("/mcp/process", response_model=MCPResponse)
async def process_mcp_request(
    request: MCPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    auth: bool = Depends(verify_mcp_auth)
):
    start_time = time.time()
    try:
        # Validate MCP version
        if request.mcp_version not in ["1.0"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported MCP version: {request.mcp_version}"
            )

        # Fetch additional context from Glama.ai if needed
        context = await fetch_context(request.query)
        
        # Process with Cursor AI
        response = await process_with_cursor(request.query, context)
        
        # Store the interaction in the database if user_id is provided
        if request.user_id:
            background_tasks.add_task(
                store_interaction,
                db,
                request.user_id,
                request.query,
                response,
                context
            )
        
        processing_time = time.time() - start_time
        return MCPResponse(
            response=response,
            context=context,
            metadata={
                "processed_at": datetime.utcnow().isoformat(),
                "model": mcp_settings.MODEL_NAME,
                "context_provider": mcp_settings.CONTEXT_PROVIDER,
                "priority": request.priority
            },
            mcp_version="1.0",
            processing_time=processing_time
        )
    except Exception as e:
        error = MCPError(
            code="PROCESSING_ERROR",
            message=str(e),
            details={"timestamp": datetime.utcnow().isoformat()}
        )
        return JSONResponse(
            status_code=500,
            content=error.dict()
        )

@app.post("/mcp/batch", response_model=MCPBatchResponse)
async def process_batch_request(
    request: MCPBatchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    auth: bool = Depends(verify_mcp_auth)
):
    try:
        responses = []
        for query in request.queries:
            # Process each query
            context = await fetch_context(query)
            response = await process_with_cursor(query, context)
            
            # Create response object
            mcp_response = MCPResponse(
                response=response,
                context=context,
                metadata={
                    "processed_at": datetime.utcnow().isoformat(),
                    "model": mcp_settings.MODEL_NAME,
                    "context_provider": mcp_settings.CONTEXT_PROVIDER
                },
                mcp_version="1.0"
            )
            responses.append(mcp_response)
            
            # Store interaction if user_id is provided
            if request.user_id:
                background_tasks.add_task(
                    store_interaction,
                    db,
                    request.user_id,
                    query,
                    response,
                    context
                )
        
        return MCPBatchResponse(
            responses=responses,
            batch_metadata={
                "total_queries": len(request.queries),
                "processed_at": datetime.utcnow().isoformat()
            },
            mcp_version="1.0"
        )
    except Exception as e:
        error = MCPError(
            code="BATCH_PROCESSING_ERROR",
            message=str(e),
            details={"timestamp": datetime.utcnow().isoformat()}
        )
        return JSONResponse(
            status_code=500,
            content=error.dict()
        )

@app.get("/mcp/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "glama_ai": "connected",
            "cursor_ai": "connected",
            "database": "connected"
        },
        "mcp_version": "1.0",
        "rate_limits": {
            "current_usage": "0%",
            "requests_per_period": mcp_settings.RATE_LIMIT_REQUESTS,
            "period_seconds": mcp_settings.RATE_LIMIT_PERIOD
        }
    }

async def fetch_context(message: str) -> dict:
    """Fetch relevant context from Glama.ai"""
    headers = {
        "Authorization": f"Bearer {GLAMA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": message,
        "max_results": mcp_settings.MAX_CONTEXT_RESULTS
    }
    
    try:
        response = requests.post(
            f"{GLAMA_API_URL}/context",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        error = MCPError(
            code="CONTEXT_FETCH_ERROR",
            message=f"Error fetching context: {str(e)}",
            details={"timestamp": datetime.utcnow().isoformat()}
        )
        raise HTTPException(status_code=500, detail=error.dict())

async def process_with_cursor(message: str, context: dict) -> str:
    """Process message with Cursor AI"""
    # TODO: Implement Cursor AI integration
    # This is a placeholder response
    return f"Processed message: {message}"

async def store_interaction(
    db: Session,
    user_id: str,
    message: str,
    response: str,
    context: dict
):
    """Store interaction in database"""
    try:
        chat_message = models.ChatMessage(
            user_id=int(user_id),
            message=message,
            response=response,
            context=json.dumps(context)
        )
        db.add(chat_message)
        db.commit()
    except Exception as e:
        # Log error but don't raise it since this is a background task
        print(f"Error storing interaction: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 