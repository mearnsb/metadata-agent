from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class Message(BaseModel):
    """Model for a chat message"""
    id: int
    role: str
    name: str
    content: str
    timestamp: str

class ResponseContent(BaseModel):
    """Model for the response content"""
    content: List[Message]
    role: str = "assistant"
    chat_history: List[Message] = []

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    metadata: Dict[str, Any] = {}

class ChatResponse(BaseModel):
    response: ResponseContent
    session_id: str
    metadata: Dict[str, Any]
    chat_history: List[Message] = []
    error: bool = False
    cleaned_message: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "response": {
                    "content": "Sample response",
                    "role": "assistant",
                    "chat_history": [
                        {
                            "id": 1,
                            "role": "user",
                            "name": "User",
                            "content": "Sample message",
                            "timestamp": "2024-02-04T10:00:00"
                        }
                    ]
                },
                "session_id": "test_session",
                "metadata": {"source": "test"},
                "chat_history": [
                    {
                        "id": 1,
                        "role": "user",
                        "name": "User",
                        "content": "Sample message",
                        "timestamp": "2024-02-04T10:00:00"
                    }
                ],
                "cleaned_message": True
            }
        }

class ClearRequest(BaseModel):
    session_id: str

class ClearResponse(BaseModel):
    success: bool
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Successfully cleared session test_session"
            }
        } 