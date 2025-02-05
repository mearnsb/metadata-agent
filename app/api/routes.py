from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging
from ..models.chat import (
    ChatRequest, 
    ChatResponse, 
    Message, 
    ResponseContent,
    ClearRequest,
    ClearResponse
)
from ..core.session import SessionManager
from ..services.chat_service import ChatService
import traceback

router = APIRouter()
logger = logging.getLogger(__name__)
chat_service = ChatService()

@router.get("/hello")
async def hello_world():
    return JSONResponse(content={"message": "Hello, World!"})

@router.post("/api/v1/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        logger.info(f"Received chat request: {request}")
        
        # Get response from service
        response = await chat_service.process_chat(
            message=request.message,
            session_id=request.session_id,
            metadata=request.metadata
        )
        
        logger.info("Successfully processed chat request")
        logger.debug(f"Response: {response}")
        
        # The response is already a validated dict from model_dump()
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Create error response using models
        empty_chat_history = []
        error_response = ResponseContent(
            content=f"Error processing request: {str(e)}",
            role="assistant",
            chat_history=empty_chat_history
        )
        
        error_chat_response = ChatResponse(
            response=error_response,
            session_id=request.session_id,
            metadata=request.metadata,
            chat_history=empty_chat_history,
            error=True,
            cleaned_message=False
        )
        
        raise HTTPException(
            status_code=500,
            detail=error_chat_response.model_dump()
        )

@router.post("/clear", response_model=ClearResponse)
async def clear_session(request: ClearRequest) -> ClearResponse:
    try:
        session_manager = SessionManager()
        success = session_manager.clear_session(request.session_id)
        
        if success:
            return ClearResponse(
                success=True,
                message=f"Successfully cleared session {request.session_id}"
            )
        else:
            return ClearResponse(
                success=False,
                message=f"Session {request.session_id} not found"
            )

    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        return ClearResponse(
            success=False,
            message=f"Error clearing session: {str(e)}"
        )

@router.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy"}) 