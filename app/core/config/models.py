import os
from vertexai.generative_models import HarmBlockThreshold, HarmCategory
from typing import Dict, List, Any

class ModelConfigs:
    @staticmethod
    def get_safety_settings() -> Dict[HarmCategory, HarmBlockThreshold]:
        return {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }

    @staticmethod
    def get_cerebras_config() -> List[Dict[str, Any]]:
        return [{
            "model": "llama3.3-70b",
            "api_key": os.environ.get("CEREBRAS_API_KEY"),
            "api_type": "cerebras",
            "stream": False,
            "base_url": "https://api.cerebras.ai/v1",
            "temperature": 0.0
        }]

    @staticmethod
    def get_gemini_config(project_id: str) -> List[Dict[str, Any]]:
        return [{
            "model": "gemini-2.0-flash-exp",
            "api_type": "google",
            "project_id": project_id,
            "location": "us-central1",
            "google_application_credentials": "/Users/brian/key.json",
            "api_rate_limit": 1,
            "safety_settings": ModelConfigs.get_safety_settings(),
            "temperature": 0.0,
            "max_tokens": 7000
        }]

    # Add other model configs...

    @classmethod
    def get_config_list(cls, model_type: str = "gemini", project_id: str = None) -> Dict[str, List[Dict[str, Any]]]:
        configs = {
            "cerebras": cls.get_cerebras_config(),
            "gemini": cls.get_gemini_config(project_id),
            # Add other model types...
        }
        return {"config_list": configs.get(model_type, cls.get_gemini_config(project_id))} 