from typing import List, Dict, Any
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, role: str, name: str):
        self.role = role
        self.name = name
        self.system_message = ""
    
    @abstractmethod
    async def process_message(self, message: str, chat_history: List[Dict[str, str]]) -> str:
        """
        Process a message and return a response
        
        Args:
            message (str): The input message to process
            chat_history (List[Dict[str, str]]): Previous messages in the conversation
            
        Returns:
            str: The agent's response
        """
        pass
    
    def should_participate(self, message: str) -> bool:
        """
        Determine if this agent should participate in processing the message
        
        Args:
            message (str): The message to evaluate
            
        Returns:
            bool: True if the agent should participate, False otherwise
        """
        return True  # Default to participating
    
    def get_system_message(self) -> str:
        """Get the agent's system message"""
        return self.system_message
    
    def set_system_message(self, message: str):
        """Set the agent's system message"""
        self.system_message = message

class SQLAgent(BaseAgent):
    """Agent specialized in SQL operations"""
    
    def __init__(self):
        super().__init__(role="sql_assistant", name="SQL Assistant")
        self.set_system_message("I am a SQL expert that helps with database queries.")
    
    async def process_message(self, message: str, chat_history: List[Dict[str, str]]) -> str:
        # TODO: Implement actual SQL processing
        return f"SQL Assistant processed: {message}"

class JobAgent(BaseAgent):
    """Agent specialized in job operations"""
    
    def __init__(self):
        super().__init__(role="job_assistant", name="Job Assistant")
        self.set_system_message("I help manage and execute jobs.")
    
    async def process_message(self, message: str, chat_history: List[Dict[str, str]]) -> str:
        # TODO: Implement actual job processing
        return f"Job Assistant processed: {message}"

class ReviewerAgent(BaseAgent):
    """Agent that reviews and summarizes conversations"""
    
    def __init__(self):
        super().__init__(role="reviewer", name="Reviewer")
        self.set_system_message("I review conversations and provide summaries.")
    
    async def process_message(self, message: str, chat_history: List[Dict[str, str]]) -> str:
        # TODO: Implement actual review processing
        return f"Reviewer processed: {message}" 