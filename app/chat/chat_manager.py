import autogen
import copy
from typing import Tuple, Dict, Any, List
from dataclasses import dataclass
import logging
from ..preprocessing.message_redact import MessageRedact
from ..agents.agent_factory import create_agents
from datetime import datetime
import traceback
import json

logger = logging.getLogger(__name__)

@dataclass
class ChatResult:
    response: Dict[str, Any]
    participants: List[str]
    chat_history: List[Dict[str, Any]]
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert ChatResult to dictionary"""
        try:
            logger.info("Converting ChatResult to dictionary")
            logger.info(f"Response structure: {self.response}")
            logger.info(f"Number of participants: {len(self.participants)}")
            logger.info(f"Number of chat history messages: {len(self.chat_history)}")
            
            return {
                "response": self.response,
                "participants": self.participants,
                "chat_history": self.chat_history,
                "metadata": self.metadata or {}
            }
            
        except Exception as e:
            logger.error(f"Error converting ChatResult to dictionary: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "response": {
                    "content": "Error formatting response",
                    "role": "assistant",
                    "chat_history": []
                },
                "participants": [],
                "chat_history": [],
                "metadata": {"error": True, "error_message": str(e)}
            }

class ChatManager:
    def __init__(self, llm_config: Dict[str, Any]):
        """Initialize the chat manager with LLM configuration"""
        self.llm_config = llm_config
        self.history = []
        
        # Create all agents
        self.agents = create_agents(llm_config)
        
        # Extract individual agents for easy reference
        self.user_proxy = self.agents["user_proxy"]
        self.sql_assistant = self.agents["sql_assistant"]
        self.job_assistant = self.agents["job_assistant"]
        self.executor = self.agents["executor"]
        self.reviewer_assistant = self.agents["reviewer_assistant"]
        
        # Define allowed transitions
        allowed_transitions = {
            self.user_proxy: [self.sql_assistant, self.job_assistant, self.reviewer_assistant],
            self.sql_assistant: [self.executor, self.user_proxy],
            self.job_assistant: [self.executor, self.user_proxy],
            self.executor: [self.reviewer_assistant, self.user_proxy],
            self.reviewer_assistant: [self.user_proxy],
        }
        
        # Create the group chat with specified transitions
        self.groupchat = autogen.GroupChat(
            agents=[
                self.user_proxy,
                self.sql_assistant,
                self.job_assistant,
                self.executor,
                self.reviewer_assistant
            ],
            messages=[],
            max_round=5,
            speaker_transitions_type="allowed",
            allowed_or_disallowed_speaker_transitions=allowed_transitions,
            send_introductions=True
        )
        
        # Create the group chat manager
        self.manager = autogen.GroupChatManager(
            groupchat=self.groupchat,
            llm_config=self.llm_config,
            is_termination_msg=lambda x: "TERMINATE" in x.get("content", "")
        )

    async def group_chat(self, message: str, agents: List[Any], preprocessing: Any) -> ChatResult:
        """Run a group chat session"""
        try:
            logger.info(f"Starting group chat with message: {message}")
            
            # Preprocess the message
            processed_message = await preprocessing.process(message)
            logger.info(f"Processed message: {processed_message}")
            
            # Use the chat method which properly handles message history
            chat_response, manager = self.chat(processed_message)
            
            # Get messages from the manager
            tmp_messages = copy.deepcopy(manager.groupchat.messages)
            end_window = len(tmp_messages)
            start_window = 0
            retain_messages = 11

            # Filter out intro messages
            messages = []
            intro_string = 'We have assembled a great team today'
            
            for msg in tmp_messages:
                if not isinstance(msg, dict) or intro_string in msg.get('content', ''):
                    continue
                
                content = msg.get('content', '')
                if not content or "Hello everyone." in content:
                    continue
                
                messages.append({
                    "id": len(messages) + 1,
                    "role": msg.get("role", "assistant"),
                    "name": msg.get("name", "Unknown"),
                    "content": content,
                    "timestamp": str(datetime.now())
                })

            # Keep only recent messages
            if len(messages) > retain_messages:
                start_window = len(messages) - retain_messages
                messages = messages[start_window:]
            
            logger.info(f"Processed {len(messages)} messages")
            
            # Create ChatResult with the messages
            result = ChatResult(
                response={
                    "content": messages,
                    "role": "assistant",
                    "chat_history": messages
                },
                participants=[agent.name for agent in self.groupchat.agents],
                chat_history=messages,
                metadata={"timestamp": str(datetime.now())}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in group chat: {str(e)}")
            logger.error(traceback.format_exc())
            return ChatResult(
                response={
                    "content": [],
                    "role": "assistant",
                    "chat_history": []
                },
                participants=[],
                chat_history=[],
                metadata={"error": True, "error_message": str(e)}
            )

    def _format_chat_history(self) -> List[Dict[str, Any]]:
        """Format the chat history as a list of messages"""
        messages = []
        try:
            # Get messages from groupchat
            if hasattr(self.manager, 'groupchat') and hasattr(self.manager.groupchat, 'messages'):
                chat_messages = self.manager.groupchat.messages
                logger.debug(f"Raw chat messages: {chat_messages}")
                
                for i, m in enumerate(chat_messages):
                    if not m or not isinstance(m, dict):
                        logger.warning(f"Skipping invalid message format: {m}")
                        continue
                        
                    content = m.get('content', '')
                    if not content or "Hello everyone." in content:
                        continue
                    
                    # Format each message
                    message = {
                        "id": i + 1,
                        "role": m.get("role", "assistant"),
                        "name": m.get("name", "Unknown"),
                        "content": content,
                        "timestamp": str(datetime.now())
                    }
                    messages.append(message)
                    logger.debug(f"Formatted message: {message}")
                
            return messages
            
        except Exception as e:
            logger.error(f"Error formatting chat history: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    def _extract_response_text(self, chat_response: Any) -> str:
        """Extract text from chat response"""
        try:
            # If response is a tuple, get the first element
            if isinstance(chat_response, tuple):
                chat_response = chat_response[0]
            
            # If response is a list, get the last message
            if isinstance(chat_response, list) and chat_response:
                # Get last non-empty message
                for msg in reversed(chat_response):
                    if msg and isinstance(msg, dict) and msg.get('content'):
                        chat_response = msg
                        break
            
            # Extract content from message object
            if isinstance(chat_response, dict):
                content = chat_response.get('content', '')
                return str(content)[:1000] if content else ''
            
            # If response is already a string
            if isinstance(chat_response, str):
                return chat_response[:1000]
            
            # For any other type, convert to string
            return str(chat_response)[:1000]
            
        except Exception as e:
            logger.error(f"Error extracting response text: {str(e)}")
            logger.error(traceback.format_exc())
            return "Error processing response"

    def get_recent_context(self) -> str:
        """Get recent conversation context"""
        messages = self._format_chat_history()
        return "\n".join([f"{m['name']}: {m['content']}" for m in messages])

    def chat(self, prompt: str) -> Tuple[Any, Any]:
        """Handle chat with proper message history and initialization"""
        try:
            clean_transform = MessageRedact()
            tmp_messages = copy.deepcopy(self.manager.groupchat.messages)
            end_window = len(tmp_messages)
            
            # retain window of 11 messages
            start_window = max(0, end_window - 11)  # Keep last 5 messages

            # Create intro message with valid agent name
            intro_message = {
                'content': self.groupchat.introductions_msg(),
                'role': 'user',
                'name': self.user_proxy.name  # Use a valid agent name
            }
            
            # Process existing messages if any
            if tmp_messages:
                processed_messages = clean_transform.apply_transform(
                    tmp_messages[start_window:end_window]
                )
                processed_messages.insert(0, intro_message)
            else:
                # If no messages, just start with intro
                processed_messages = [intro_message]

            try:
                # Try to resume existing chat
                last_agent, last_message = self.manager.resume(messages=processed_messages)
            except Exception as e:
                logger.warning(f"Could not resume chat: {str(e)}")
                # If resume fails, start fresh
                self.manager.groupchat.messages = [intro_message]
                last_agent = self.user_proxy
                last_message = None

            # Initiate chat with the prompt
            chat_result = self.user_proxy.initiate_chat(
                recipient=self.manager,
                message=prompt,
                clear_history=False,
                max_rounds=7
            )
            
            return chat_result, self.manager

        except Exception as e:
            logger.error(f"Error in chat method: {str(e)}")
            logger.error(traceback.format_exc())
            # Return empty result if error
            return [], self.manager 