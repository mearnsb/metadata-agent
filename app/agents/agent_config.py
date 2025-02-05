import os
import google.auth
import google.auth.transport.requests
from vertexai.generative_models import HarmBlockThreshold, HarmCategory
from typing import Dict, Any, List
from ..core.config.environment import Environment
import logging

logger = logging.getLogger(__name__)

class ModelConfig:
    """Configuration for language models"""
    
    @staticmethod
    def get_openai_config() -> Dict[str, Any]:
        """Get OpenAI configuration"""
        env_vars = Environment.get_required_vars()
        config_list = [{
            "model": os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
            "api_key": env_vars.get("OPENAI_API_KEY"),
            "api_type": "openai",
            "temperature": 0.0,
            "max_tokens": 4096,
            "top_p": 1.0,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
            "stream": False
        }]
        return {"config_list": config_list}

    @staticmethod
    def get_gemini_config() -> Dict[str, Any]:
        """Get Gemini configuration"""
        try:
            logger.info("Initializing Gemini configuration")
            # Setup auth like in notebook
            scopes = ["https://www.googleapis.com/auth/cloud-platform"]
            creds, project = google.auth.default(scopes)
            auth_req = google.auth.transport.requests.Request()
            creds.refresh(auth_req)
            
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "sample-1474250537486")
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/Users/brian/key.json")
            
            config_list = [{
                "model": os.getenv("GOOGLE_MODEL_NAME", "gemini-2.0-flash-exp"),
                "api_type": "google",
                "project_id": project_id,
                "location": os.getenv("GOOGLE_MODEL_REGION", "us-central1"),
                "google_application_credentials": credentials_path,
                "api_rate_limit": 1,
                "safety_settings": ModelConfig.get_safety_settings(),
                "temperature": 0.0,
                "max_tokens": 7000,
            }]
            logger.info(f"Gemini config created successfully with project_id: {project_id}")
            return {"config_list": config_list}
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud credentials: {str(e)}")
            raise ValueError(f"Failed to initialize Google Cloud credentials: {str(e)}")

    @staticmethod
    def get_anthropic_config() -> Dict[str, Any]:
        """Get Anthropic configuration"""
        config_list = [{
            "model": "claude-3-5-sonnet-20240620",
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "api_type": "anthropic",
        }]
        return {"config_list": config_list}

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get default LLM configuration based on environment setting"""
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        logger.info(f"Getting default config with provider: {provider}")
        
        if provider == "google":
            logger.info("Using Google Gemini configuration")
            return ModelConfig.get_gemini_config()
        elif provider == "anthropic":
            logger.info("Using Anthropic configuration")
            return ModelConfig.get_anthropic_config()
        else:
            logger.info(f"Using OpenAI configuration (provider was: {provider})")
            return ModelConfig.get_openai_config()

    @staticmethod
    def get_safety_settings() -> Dict[str, Any]:
        """Get safety settings for the model (only used by Gemini)"""
        return {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }

    @staticmethod
    def setup_google_auth():
        """Setup Google authentication"""
        scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        creds, project = google.auth.default(scopes)
        auth_req = google.auth.transport.requests.Request()
        creds.refresh(auth_req)
        return creds

    @staticmethod
    def get_llm_config(project_id: str = None) -> Dict[str, Any]:
        """Get LLM configuration"""
        return {
            "model": "gemini-2.0-flash-exp",
            "api_type": "google",
            "project_id": project_id,
            "location": "us-central1",
            "google_application_credentials": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            "api_rate_limit": 1,
            "safety_settings": ModelConfig.get_safety_settings(),
            "temperature": 0.0,
            "max_tokens": 7000
        }

# Pricing constants
PROMPT_PRICE_PER_1K = 0.000125
COMPLETION_TOKEN_PRICE_PER_1K = 0.000375 