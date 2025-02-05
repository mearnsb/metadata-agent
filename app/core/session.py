from typing import Dict, Any
import logging
from ..chat.chat_manager import ChatManager
from ..agents.agent_config import ModelConfig

logger = logging.getLogger(__name__)

class SessionManager:
    _instance = None
    _sessions: Dict[str, ChatManager] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_session(cls, session_id: str) -> ChatManager:
        if session_id not in cls._sessions:
            logger.info(f"Creating new session for {session_id}")
            llm_config = ModelConfig.get_llm_config()
            cls._sessions[session_id] = ChatManager(llm_config)
        return cls._sessions[session_id]

    @classmethod
    def clear_session(cls, session_id: str) -> bool:
        try:
            if session_id in cls._sessions:
                del cls._sessions[session_id]
                logger.info(f"Cleared session {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error clearing session {session_id}: {str(e)}")
            return False 