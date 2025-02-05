from pydantic import BaseModel
from typing import Optional, Dict, Any

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: Dict[str, str]
    session_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    cleaned_message: bool

class ClearRequest(BaseModel):
    session_id: str

class ClearResponse(BaseModel):
    success: bool
    message: str 