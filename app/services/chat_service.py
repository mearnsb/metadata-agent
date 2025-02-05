from typing import Dict, Any
import logging
from ..models.chat import Message, ResponseContent, ChatResponse
from ..preprocessing.message_redact import MessageRedact
from ..agents.agent_factory import create_group_chat_agents
from ..chat.chat_manager import ChatManager
from ..preprocessing.assistants import PreprocessingAssistants
from ..agents.agent_config import ModelConfig
import traceback
import json
import os

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling group chat operations"""
    
    def __init__(self):
        """Initialize chat service with agents and managers"""
        self.previous_history = []
        self.clean_transform = MessageRedact()
        
        try:
            # Get LLM configuration based on environment setting
            provider = os.getenv("LLM_PROVIDER", "openai").lower()
            logger.info(f"Initializing ChatService with LLM provider: {provider}")
            
            llm_config = ModelConfig.get_default_config()
            
            # Initialize chat components
            self.chat_manager = ChatManager(llm_config=llm_config)
            self.preprocessing = PreprocessingAssistants(config_list=llm_config.get("config_list")[0])
            self.agents = create_group_chat_agents()
            
            logger.info("ChatService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChatService: {str(e)}")
            raise
        
    async def process_group_chat(self, message: str) -> dict:
        """Process a message through the group chat system"""
        try:
            # Clean and redact the message
            cleaned_message = self.clean_transform(message)
            self.previous_history.append(cleaned_message)
            
            # Process through group chat
            chat_result = await self.chat_manager.group_chat(
                message=cleaned_message,
                agents=self.agents,
                preprocessing=self.preprocessing
            )
            
            return {
                "response": chat_result.response,
                "participants": chat_result.participants,
                "history_length": len(self.previous_history),
                "original_message": message,
                "cleaned_message": cleaned_message
            }
        except Exception as e:
            logger.error(f"Error in group chat: {str(e)}")
            raise

    async def process_chat(self, message: str, session_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a chat message"""
        try:
            logger.info(f"Processing chat message: {message}")
            result = await self.chat_manager.group_chat(
                message=message,
                agents=self.agents,
                preprocessing=self.preprocessing
            )
            
            # Log the chat history
            logger.debug(f"Chat history from result: {result.chat_history}")
            
            # Create response using the chat history directly
            response = ChatResponse(
                response=ResponseContent(
                    content=result.chat_history,  # Use chat history directly
                    role="assistant",
                    chat_history=result.chat_history
                ),
                session_id=session_id,
                metadata=metadata,
                chat_history=result.chat_history,
                error=False,
                cleaned_message=True
            )
            
            # Log and return
            response_dict = response.model_dump()
            logger.debug(f"Final response: {response_dict}")
            return response_dict

        except Exception as e:
            logger.error(f"Error processing chat: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "response": {
                    "content": [],
                    "role": "assistant",
                    "chat_history": []
                },
                "session_id": session_id,
                "metadata": metadata,
                "chat_history": [],
                "error": True
            } 