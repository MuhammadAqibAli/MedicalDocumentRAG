import json
import logging
import requests
from openai import OpenAI
from langchain.llms.base import LLM
from typing import Any, Dict, List, Optional
from .openrouter_config import OPENROUTER_BASE_URL, OPENROUTER_API_KEY, OPENROUTER_HEADERS, OPENROUTER_MODELS

logger = logging.getLogger(__name__)

class OpenRouterLLM(LLM):
    """LangChain wrapper for OpenRouter models."""
    
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 1024
    
    def __init__(self, model_name: str, **kwargs):
        """Initialize OpenRouter LLM."""
        if model_name not in OPENROUTER_MODELS:
            raise ValueError(f"Model {model_name} not found in available OpenRouter models")
        
        self.model_name = model_name
        self.model_config = OPENROUTER_MODELS[model_name]
        
        # Override defaults with any provided kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
            
        super().__init__(**kwargs)
    
    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "openrouter"
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Call the OpenRouter API."""
        try:
            # Get the full model ID from our config
            model_id = self.model_config["model_id"]
            
            # Use OpenAI client for better handling
            client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)
            
            # Create the completion
            completion = client.chat.completions.create(
                extra_headers=OPENROUTER_HEADERS,
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
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get identifying parameters."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

def get_openrouter_llm(model_name: str, **kwargs) -> OpenRouterLLM:
    """Get an instance of OpenRouterLLM."""
    return OpenRouterLLM(model_name=model_name, **kwargs)