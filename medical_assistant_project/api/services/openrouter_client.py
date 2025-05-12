import json
import logging
import requests
from openai import OpenAI
from typing import Any, Dict, List, Optional, Union
from .openrouter_config import OPENROUTER_BASE_URL, OPENROUTER_API_KEY, OPENROUTER_HEADERS, OPENROUTER_MODELS

logger = logging.getLogger(__name__)

class OpenRouterLLM:
    """Simple wrapper for OpenRouter models."""
    
    def __init__(self, model_name: str, temperature: float = 0.7, max_tokens: int = 1024):
        """Initialize with model name and optional parameters."""
        if model_name not in OPENROUTER_MODELS:
            raise ValueError(f"Model {model_name} not found in available OpenRouter models")
        
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model_config = OPENROUTER_MODELS[model_name]
        
        # Validate API key
        if not OPENROUTER_API_KEY or OPENROUTER_API_KEY.strip() == "":
            raise ValueError("OpenRouter API key is missing or empty")
    
    def invoke(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        """Call the OpenRouter API with a prompt and return the response."""
        try:
            # Get the full model ID from our config
            model_id = self.model_config["model_id"]
            
            # Log request details for debugging (excluding API key)
            logger.debug(f"OpenRouter request: model={model_id}, base_url={OPENROUTER_BASE_URL}, api_key={OPENROUTER_API_KEY}")
            

            # Use OpenAI client for better handling
            client = OpenAI(
                base_url=OPENROUTER_BASE_URL,
                api_key=OPENROUTER_API_KEY,
                ##default_headers=OPENROUTER_HEADERS  # Set default headers here
            )
            
            # Create the completion
            completion = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stop=stop
            )
            
            # Extract the response text
            response_text = completion.choices[0].message.content
            return response_text
            
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            raise RuntimeError(f"OpenRouter API call failed: {e}")

def get_openrouter_llm(model_name: str, **kwargs) -> OpenRouterLLM:
    """Get an instance of OpenRouterLLM."""
    return OpenRouterLLM(model_name=model_name, **kwargs)
