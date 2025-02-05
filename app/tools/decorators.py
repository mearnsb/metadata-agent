from functools import wraps
from typing import Callable, Any

def register_tool(executor: Any = None, assistant: Any = None, description: str = None):
    """Decorator to register a tool with both executor and assistant"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
            
        if executor:
            executor.register_for_execution()(wrapper)
            executor.register_for_llm()(wrapper)
            
        if assistant and description:
            assistant.register_for_llm(description=description)(wrapper)
            
        return wrapper
    return decorator 