import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenRouter Configuration
# Try to get API key from environment variable first, then fall back to hardcoded value
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
SITE_URL = "https://medical-document-assistant.nz"
SITE_NAME = "NZ Medical Document Assistant"

# Headers for OpenRouter API requests
OPENROUTER_HEADERS = {
    "HTTP-Referer": SITE_URL,
    "X-Title": SITE_NAME
}

# Available OpenRouter models
OPENROUTER_MODELS = {
    "gpt-4o": {
        "model_id": "openai/gpt-4o",
        "provider": "openai",
        "display_name": "GPT-4o",
        "supports_images": True,
        "max_tokens": 4096
    },
    "gpt-4.1": {
        "model_id": "openai/gpt-4.1",
        "provider": "openai",
        "display_name": "GPT-4.1",
        "supports_images": True,
        "max_tokens": 4096
    },
    "gpt-4.1-mini": {
        "model_id": "openai/gpt-4.1-mini",
        "provider": "openai",
        "display_name": "GPT-4.1 Mini",
        "supports_images": True,
        "max_tokens": 4096
    },
    "chatgpt-4o-latest": {
        "model_id": "openai/chatgpt-4o-latest",
        "provider": "openai",
        "display_name": "ChatGPT-4o Latest",
        "supports_images": True,
        "max_tokens": 4096
    },
    "gemini-2.5-pro-preview": {
        "model_id": "google/gemini-2.5-pro-preview",
        "provider": "google",
        "display_name": "Gemini 2.5 Pro Preview",
        "supports_images": True,
        "max_tokens": 4096
    },
    "deepseek-prover-v2": {
        "model_id": "deepseek/deepseek-prover-v2:free",
        "provider": "deepseek",
        "display_name": "DeepSeek Prover V2",
        "supports_images": False,
        "max_tokens": 4096
    }
}
