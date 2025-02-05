import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class Environment:
    _is_initialized = False

    @classmethod
    def initialize(cls):
        """Initialize environment variables"""
        if not cls._is_initialized:
            # Find .env file
            env_path = Path(__file__).parent.parent.parent.parent / '.env'
            if not env_path.exists():
                raise FileNotFoundError(f".env file not found at {env_path}")
            
            # Load environment variables
            load_dotenv(env_path)
            cls._is_initialized = True
            os.environ["AUTOGEN_USE_DOCKER"] = "False"  # Disable Docker globally for autogen
            
            # Log important configurations
            logger.info(f"Environment initialized from: {env_path}")
            logger.info(f"LLM_PROVIDER set to: {os.getenv('LLM_PROVIDER', 'not set')}")
            logger.info(f"GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'not set')}")

    @classmethod
    def get_required_vars(cls) -> Dict[str, str]:
        """Get required environment variables"""
        cls.initialize()
        
        # Add LLM-specific required variables
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        required_vars = {
            "DQ_URL": os.getenv("DQ_URL"),
            "DQ_CREDENTIAL": os.getenv("DQ_CREDENTIAL"),
            "DQ_USERNAME": os.getenv("DQ_USERNAME"),
            "DQ_TENANT": os.getenv("DQ_TENANT"),
            "DQ_CREDENTIAL": os.getenv("DQ_CREDENTIAL"),
            "LLM_PROVIDER": provider,
        }
        
        # Log DQ configuration (excluding sensitive info)
        logger.info("DQ Configuration:")
        logger.info(f"URL: {required_vars['DQ_URL']}")
        logger.info(f"Username: {required_vars['DQ_USERNAME']}")
        logger.info(f"Tenant: {required_vars['DQ_TENANT']}")
        
        # Add provider-specific requirements
        if provider == "google":
            required_vars.update({
                "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
                "GOOGLE_CLOUD_PROJECT": os.getenv("GOOGLE_CLOUD_PROJECT"),
            })
        elif provider == "openai":
            required_vars.update({
                "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            })
        elif provider == "anthropic":
            required_vars.update({
                "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
            })
        
        missing = [k for k, v in required_vars.items() if not v]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
            
        return required_vars

    @classmethod
    def validate(cls):
        """Validate all required environment variables are set"""
        return cls.get_required_vars() 