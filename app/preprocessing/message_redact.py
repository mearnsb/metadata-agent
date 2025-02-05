import json
import copy
import re
from typing import Dict, List, Tuple

class MessageRedact:
    """Class for cleaning and transforming chat messages"""
    
    def __init__(self):
        self._content_wrapper_pattern = r"~~~.*?~~~"
        self._replacement_string = "TRUNCATED_MESSAGE"

    def __call__(self, message: str) -> str:
        """
        Clean and transform a single message string
        
        Args:
            message (str): The input message to clean
            
        Returns:
            str: The cleaned message
        """
        if not message or not isinstance(message, str):
            return ""
        
        # Truncate long messages
        if len(message) > 1000:
            message = message[:1000]
            
        # Replace content between ~~~ markers
        cleaned = re.sub(self._content_wrapper_pattern, 
                        self._replacement_string, 
                        message, 
                        flags=re.DOTALL)
        
        return cleaned.strip()

    def apply_transform(self, messages: List[Dict]) -> List[Dict]:
        """
        Transform a list of message dictionaries
        
        Args:
            messages (List[Dict]): List of message dictionaries to transform
            
        Returns:
            List[Dict]: Transformed messages
        """
        temp_messages = copy.deepcopy(messages)

        total_tool_calls = 0
        total_tool_responses = 0
        counter = 0
        
        for m in temp_messages:
            if "tool_calls" in m:
                total_tool_calls += len(m["tool_calls"])
                content_string = "Context from previous tool calls: "
                
                for i in m["tool_calls"]:
                    content_string += "\n function name: " + i['function']['name']
                    content_string += "\n function arguments: " + json.dumps(i['function']['arguments'])
                
                m.pop("tool_calls")
                m['role'] = "user"
                m["content"] = content_string

            if "tool_responses" in m:
                total_tool_responses += len(m["tool_responses"])
                content_string = "Context from previous tool response:"
                
                for j in m["tool_responses"]:
                    content_string += json.dumps(j['content'])
                    
                m["content"] = content_string
                m['role'] = "user"
                m.pop("tool_responses")
            
            # Handle message content
            if isinstance(m["content"], str):
                counter += 1
                if counter < 5:
                    m["content"] = m["content"][:600]
                else:
                    m["content"] = m["content"][:1000]
            
            elif isinstance(m["content"], list):
                for item in m["content"]:
                    if item["type"] == "text":
                        item["text"] = re.sub(
                            self._content_wrapper_pattern, 
                            self._replacement_string, 
                            item["text"], 
                            flags=re.DOTALL
                        )

        # Add final message
        temp_messages.append({
            'content': 'Thank you. I will review this information and get back to you.',
            'role': 'user',
            'name': 'Admin_User'
        })
        
        return temp_messages

    def get_logs(self, pre_transform_messages: List[Dict], 
                post_transform_messages: List[Dict]) -> Tuple[str, bool]:
        """Get logs of transformation changes"""
        keys_redacted = self._count_redacted(post_transform_messages) - \
                       self._count_redacted(pre_transform_messages)
        if keys_redacted > 0:
            return f"Redacted {keys_redacted} Matching Patterns.", True
        return "", False

    def _count_redacted(self, messages: List[Dict]) -> int:
        """Count number of redacted patterns in messages"""
        count = 0
        for message in messages:
            if isinstance(message["content"], str):
                if self._replacement_string in message["content"]:
                    count += 1
            elif isinstance(message["content"], list):
                for item in message["content"]:
                    if isinstance(item, dict) and "text" in item:
                        if self._replacement_string in item["text"]:
                            count += 1
        return count 