# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Standard library imports
import os
import logging
from pathlib import Path
import datetime

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log environment variables for debugging
logger.info(f"LLM_PROVIDER from env: {os.getenv('LLM_PROVIDER')}")

# Third-party imports
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Local application imports
from app.api.routes import router
from app.core.logging import setup_logging
from app.core.session import SessionManager
from app.models.models import ChatRequest, ChatResponse, ClearRequest, ClearResponse
from app.core.config.paths import DataPaths
from app.core.config.environment import Environment
from app.services.retrieval_service import RetrievalService
from app.services.sql_service import SQLService
from app.services.chat_service import ChatService

# Setup logging
setup_logging()

# Initialize environment
Environment.initialize()

app = FastAPI(
    title="Chat API",
    version="1.0.0",
    description="API for managing chat sessions with AI agents"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize session manager
session_manager = SessionManager()

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "message": "An internal server error occurred",
            "error": str(exc)
        }
    )

# Mount the router at the root path
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    """Initialize any required resources on startup"""
    logger.info("Application starting up...")
    try:
        # Initialize any required resources
        # For example, ensure required environment variables are set
        required_env_vars = ["DQ_URL", "DQ_CREDENTIAL"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            raise ValueError(f"Missing required environment variables: {missing_vars}")
            
        # Initialize database connections if needed
        logger.info("Initializing database connections...")
        
        # Initialize any other required services
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    logger.info("Application shutting down...")
    try:
        # Clean up any resources
        logger.info("Cleaning up sessions...")
        # Clear all active sessions
        session_manager._sessions.clear()
        
        # Close any open connections
        logger.info("Closing database connections...")
        
        logger.info("Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "app_name": "Chat API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "/api/v1/chat",
            "clear": "/api/v1/clear",
            "health": "/api/v1/health",
            "test": "/test",
            "retrieve": "/retrieve",
            "sql": "/sql",
            "groupchat": "/groupchat"
        }
    }

# Add this new test endpoint
@app.get("/test")
async def test():
    """Simple test endpoint that returns a success message"""
    return {
        "status": "success",
        "message": "Server is running and accessible",
        "timestamp": datetime.datetime.now().isoformat()
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Add any additional health checks here
        # For example, check database connectivity
        return {
            "status": "healthy",
            "active_sessions": len(session_manager._sessions),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

@app.get("/retrieve")
async def test_retrieve(query: str = Query(..., description="The query to retrieve similar documents for")):
    """Test endpoint for retrieval functionality"""
    try:
        retrieval_service = RetrievalService()
        results = await retrieval_service.retrieve(query)
        return {
            "status": "success",
            "query": query,
            "results": results,
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Retrieval test failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
        )

@app.get("/sql")
async def test_sql(query: str = Query(..., description="The natural language query to convert to SQL")):
    """Test endpoint for SQL generation functionality"""
    try:
        sql_service = SQLService()
        sql_query = await sql_service.generate_sql(query)
        return {
            "status": "success",
            "natural_language_query": query,
            "generated_sql": sql_query,
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"SQL generation test failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
        )

@app.get("/groupchat")
async def test_groupchat(message: str = Query(..., description="The message to discuss in the group chat")):
    """Test endpoint for group chat functionality"""
    try:
        chat_service = ChatService()
        response = await chat_service.process_group_chat(message)
        return {
            "status": "success",
            "input_message": message,
            "chat_response": response,
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Group chat test failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=1234,
        reload=True
    )
