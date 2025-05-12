import os
import json
import re
import logging
from langchain_huggingface import HuggingFaceEndpoint
from langchain_community.llms import HuggingFacePipeline  # For local models via transformers
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from .openrouter_client import get_openrouter_llm
from .openrouter_config import OPENROUTER_MODELS

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# --- LLM Configuration Settings ---
# Environment variable to control API provider
USE_OPENROUTER = os.getenv("USE_OPENROUTER", "true").lower() == "true"
USE_HUGGINGFACE_API = os.getenv("USE_HUGGINGFACE_API", "true").lower() == "true" and not USE_OPENROUTER

# Local model paths and settings
LOCAL_MODELS_DIR = os.getenv("LOCAL_MODELS_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models"))
DEFAULT_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
LOCAL_DEVICE = os.getenv("LOCAL_MODEL_DEVICE", DEFAULT_DEVICE)
LOCAL_TORCH_DTYPE = os.getenv("LOCAL_MODEL_DTYPE", "auto")  # Options: auto, float16, bfloat16, float32

# --- Model Configuration ---
# Define available models with both API and local configurations
HUGGINGFACE_MODELS = {
    "llama3-8b-instruct": {
        "api": {
            "type": "hf_endpoint",
            "repo_id": "meta-llama/Meta-Llama-3-8B-Instruct",
            "task": "text-generation",
        }
    },
    "mistral-7b-instruct": {
        "api": {
            "type": "hf_endpoint",
            "repo_id": "mistralai/Mistral-7B-Instruct-v0.2",
            "task": "text-generation",
        }
    },
    "phi-3-mini-instruct": {
        "api": {
            "type": "hf_endpoint",
            "repo_id": "microsoft/Phi-3-mini-4k-instruct",
            "task": "text-generation",
        },
        "local": {
            "type": "hf_pipeline",
            "model_id": "microsoft/Phi-3-mini-4k-instruct",
            "device": LOCAL_DEVICE,
            "torch_dtype": LOCAL_TORCH_DTYPE,
            "max_length": 4096,
            "trust_remote_code": True,
        }
    },
    "tinyllama-1.1b-chat": {
        "api": {
            "type": "hf_endpoint",
            "repo_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            "task": "text-generation",
        },
        "local": {
            "type": "hf_pipeline",
            "model_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            "device": LOCAL_DEVICE,
            "torch_dtype": LOCAL_TORCH_DTYPE,
            "max_length": 2048,
            "trust_remote_code": True,
        }
    },
}

# Combine all available models
AVAILABLE_MODELS = {}
# Add HuggingFace models
# for model_name, config in HUGGINGFACE_MODELS.items():
#     AVAILABLE_MODELS[model_name] = {
#         "provider": "huggingface",
#         "config": config
#     }

# Add OpenRouter models
for model_name, config in OPENROUTER_MODELS.items():
    AVAILABLE_MODELS[model_name] = {
        "provider": "openrouter",
        "config": config
    }

# --- Prompt Templates ---
# Note: Adjust template based on the specific model's expected input format (e.g., Llama3 uses specific roles)
RAG_PROMPT_TEMPLATE = """
You are a helpful assistant specialized in creating documents compliant with New Zealand healthcare standards and terminology. Your tone should be formal, concise, and medically appropriate.

Generate a {content_type} about the following topic: "{topic}"

Use the following context from internal documents as your primary source:
--- CONTEXT START ---
{context}
--- CONTEXT END ---

If the context is insufficient or irrelevant to the topic, state that you are generating the content based on your general knowledge while maintaining the NZ healthcare style, but mention that internal document context was not applicable.
Generate only the {content_type} content based on the topic and context provided, provide me the content in CKEditor HTML format.
"""

FALLBACK_PROMPT_TEMPLATE = """
You are a helpful assistant specialized in creating documents compliant with New Zealand healthcare standards and terminology. Your tone should be formal, concise, and medically appropriate.

Generate a {content_type} about the following topic: "{topic}"

Generate only the {content_type} content based on the topic provided. Rely on your general knowledge of healthcare best practices, adapted for a New Zealand context where possible, provide me the content in CKEditor HTML format.
"""

CONTENT_VALIDATION_TEMPLATE = """
You are an expert reviewer for New Zealand healthcare documents. 
Evaluate if the following content is a valid {standard_type} document.

CONTENT TO EVALUATE:
--- START CONTENT ---
{content}
--- END CONTENT ---

Is this content appropriate and relevant for a {standard_type} document in a healthcare setting?
Respond with ONLY a JSON object with the following structure:
{{
    "is_valid": true/false,
    "reason": "Brief explanation of why it is or isn't valid"
}}

Do not include any text before or after the JSON object. Only return the JSON.
"""

CONTENT_COMPARISON_TEMPLATE = """
You are an expert reviewer for New Zealand healthcare documents.
Compare the following two {standard_type} documents and identify the key differences.

DOCUMENT 1:
--- START DOCUMENT 1 ---
{content1}
--- END DOCUMENT 1 ---

DOCUMENT 2:
--- START DOCUMENT 2 ---
{content2}
--- END DOCUMENT 2 ---

Please analyze and respond with ONLY a JSON object with the following structure:
{{
    "key_differences": [
        {{
            "aspect": "Name of the differing aspect",
            "document1": "How document 1 addresses this aspect",
            "document2": "How document 2 addresses this aspect"
        }}
        // Add more differences as needed
    ],
    "recommendation": "Which document is better overall and why",
    "improvement_suggestions": [
        "Suggestion 1 for improving the documents",
        "Suggestion 2 for improving the documents"
    ]
}}

Do not include any text before or after the JSON object. Only return the JSON.
"""

# Cache for loaded models to avoid reloading
_model_cache = {}

def get_llm_instance(model_name: str):
    """
    Gets an instance of the specified LLM with fallback mechanism.
    
    First tries OpenRouter if USE_OPENROUTER is True,
    then tries HuggingFace API if USE_HUGGINGFACE_API is True,
    then falls back to local model if available.
    """
    if model_name not in AVAILABLE_MODELS:
        raise ValueError(f"Model '{model_name}' is not configured.")
    
    model_info = AVAILABLE_MODELS[model_name]
    provider = model_info["provider"]
    
    # Try OpenRouter first if enabled
    if USE_OPENROUTER and provider == "openrouter":
        try:
            logger.info(f"Initializing OpenRouter for {model_name}")
            llm = get_openrouter_llm(model_name=model_name, temperature=0.7, max_tokens=1024)
            # Test the model with a simple prompt to verify it works
            ##test_response = llm.invoke("Test connection")
            logger.info(f"Successfully initialized OpenRouter for {model_name}")
            return llm
        except Exception as e:
            logger.warning(f"Failed to initialize or connect to OpenRouter for {model_name}: {e}")
            # Fall through to other options if available
    
    # If it's a HuggingFace model, try API or local
    if provider == "huggingface":
        model_config = model_info["config"]
        
        # Try HuggingFace API if enabled
        if USE_HUGGINGFACE_API and "api" in model_config:
            try:
                llm = _get_hf_endpoint_instance(model_name, model_config["api"])
                # Test the model with a simple prompt to verify it works
                _ = llm.invoke("Test connection")
                logger.info(f"Successfully initialized HuggingFace API for {model_name}")
                return llm
            except Exception as e:
                logger.warning(f"Failed to initialize or connect to HuggingFace API for {model_name}: {e}")
                # Fall through to local model if available
        
        # Try local model if available
        if "local" in model_config:
            try:
                llm = _get_local_model_instance(model_name, model_config["local"])
                logger.info(f"Successfully initialized local model for {model_name}")
                return llm
            except Exception as e:
                logger.error(f"Failed to initialize local model for {model_name}: {e}")
                raise RuntimeError(f"Could not load model {model_name} (API or local): {e}") from e
    
    # If we get here, all options failed
    raise RuntimeError(f"Could not initialize any provider for model {model_name}")

def _get_hf_endpoint_instance(model_name: str, config: dict):
    """Helper function to initialize a HuggingFace endpoint instance."""
    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if not hf_token:
        raise ValueError("HUGGINGFACEHUB_API_TOKEN environment variable not set.")
    
    llm = HuggingFaceEndpoint(
        repo_id=config["repo_id"],
        task=config.get("task", "text-generation"),
        huggingfacehub_api_token=hf_token,
        temperature=0.7,  # Adjust generation parameters
        max_new_tokens=1024,
        # Add other parameters like top_p, top_k, repetition_penalty as needed
    )
    return llm

def _get_local_model_instance(model_name: str, config: dict):
    """Helper function to initialize a local model instance using HuggingFace transformers."""
    # Check if we already have this model loaded in cache
    cache_key = f"{model_name}_{config['device']}_{config['torch_dtype']}"
    if cache_key in _model_cache:
        logger.info(f"Using cached model instance for {model_name}")
        return _model_cache[cache_key]
    
    model_id = config["model_id"]
    device = config["device"]
    torch_dtype = config["torch_dtype"]
    
    logger.info(f"Loading model {model_id} on {device} with dtype {torch_dtype}")
    
    # Determine torch dtype
    if torch_dtype == "auto":
        dtype = torch.float16 if device == "cuda" else torch.float32
    elif torch_dtype == "float16":
        dtype = torch.float16
    elif torch_dtype == "bfloat16":
        dtype = torch.bfloat16
    else:
        dtype = torch.float32
    
    try:
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=config.get("trust_remote_code", False)
        )
        
        # Load model with appropriate settings
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map=device,
            torch_dtype=dtype,
            trust_remote_code=config.get("trust_remote_code", False),
            # Add low_cpu_mem_usage=True if needed
        )
        
        # Create text generation pipeline
        text_generation_pipeline = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_length=config.get("max_length", 2048),
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            do_sample=True
        )
        
        # Create LangChain wrapper
        llm = HuggingFacePipeline(pipeline=text_generation_pipeline)
        
        # Cache the model
        _model_cache[cache_key] = llm
        
        return llm
    
    except Exception as e:
        logger.error(f"Error loading local model {model_id}: {e}")
        raise RuntimeError(f"Failed to load local model {model_id}: {e}") from e

def generate_content_with_llm(topic: str, content_type: str, model_name: str, context: str | None = None):
    """
    Generates content using the specified LLM, applying RAG or fallback logic.
    """
    llm = get_llm_instance(model_name)

    # Prepare the prompt based on whether we have context or not
    if context:
        # Format the RAG prompt manually instead of using PromptTemplate
        prompt = RAG_PROMPT_TEMPLATE.format(
            content_type=content_type,
            topic=topic,
            context=context
        )
    else:
        # Format the fallback prompt manually
        prompt = FALLBACK_PROMPT_TEMPLATE.format(
            content_type=content_type,
            topic=topic
        )

    logger.info(f"Generating content for '{topic}' ({content_type}) using {model_name}. RAG context: {'Yes' if context else 'No'}")

    try:
        # Direct invocation without LangChain
        generated_text = llm.invoke(prompt)
        
        if not generated_text or not isinstance(generated_text, str):
            logger.error(f"Unexpected LLM response format: {type(generated_text)} - {generated_text}")
            raise TypeError("Could not parse LLM response.")

        logger.info(f"Successfully generated content for '{topic}' using {model_name}.")
        return generated_text.strip()

    except Exception as e:
        logger.error(f"LLM generation failed for '{topic}' using {model_name}: {e}")
        raise RuntimeError(f"LLM generation failed: {e}") from e


def validate_content_against_type(content: str, standard_type: str, model_name: str):
    """
    Validates if the provided content is appropriate for the specified standard type.
    
    Args:
        content: The content to validate
        standard_type: The type of standard (e.g., "Policy", "Clinical Procedure")
        model_name: The LLM model to use for validation
        
    Returns:
        dict: A dictionary with validation results containing 'is_valid' and 'reason'
    """
    llm = get_llm_instance(model_name)
    
    # Format the prompt manually
    formatted_prompt = CONTENT_VALIDATION_TEMPLATE.format(
        standard_type=standard_type,
        content=content
    )
    
    try:
        validation_response = llm.invoke(formatted_prompt)
        
        # Clean up the response to ensure it's valid JSON
        validation_response = validation_response.strip()
        
        # Try to find JSON in the response using regex
        json_match = re.search(r'({.*})', validation_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            try:
                validation_result = json.loads(json_str)
                return validation_result
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}, JSON string: {json_str}")
                return {
                    "is_valid": False,
                    "reason": f"Could not parse validation response: JSON decode error"
                }
        else:
            # If regex fails, try to parse the entire response as JSON
            try:
                validation_result = json.loads(validation_response)
                return validation_result
            except json.JSONDecodeError:
                logger.error(f"Could not parse validation response: {validation_response}")
                return {
                    "is_valid": False,
                    "reason": "Could not parse validation response"
                }
            
    except Exception as e:
        logger.error(f"Error validating content: {e}")
        raise RuntimeError(f"Content validation failed: {e}") from e


def compare_standard_contents(content1: str, content2: str, standard_type: str, model_name: str):
    """
    Compares two content pieces of the same standard type.
    
    Args:
        content1: First content to compare
        content2: Second content to compare
        standard_type: The type of standard (e.g., "Policy", "Clinical Procedure")
        model_name: The LLM model to use for comparison
        
    Returns:
        dict: A dictionary with comparison results
    """
    # First validate both contents
    validation1 = validate_content_against_type(content1, standard_type, model_name)
    if not validation1.get("is_valid", False):
        return {
            "valid": False,
            "message": f"First content is not valid for {standard_type}",
            "details": validation1.get("reason", "No reason provided")
        }
    
    validation2 = validate_content_against_type(content2, standard_type, model_name)
    if not validation2.get("is_valid", False):
        return {
            "valid": False,
            "message": f"Second content is not valid for {standard_type}",
            "details": validation2.get("reason", "No reason provided")
        }
    
    # If both are valid, compare them
    llm = get_llm_instance(model_name)
    
    # Format the prompt manually
    formatted_prompt = CONTENT_COMPARISON_TEMPLATE.format(
        standard_type=standard_type,
        content1=content1,
        content2=content2
    )
    
    try:
        comparison_response = llm.invoke(formatted_prompt)
        
        # Clean up the response to ensure it's valid JSON
        comparison_response = comparison_response.strip()
        
        # Try to find JSON in the response using regex
        json_match = re.search(r'({.*})', comparison_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            try:
                comparison_result = json.loads(json_str)
                return {
                    "valid": True,
                    "comparison": comparison_result
                }
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}, JSON string: {json_str}")
                raise ValueError(f"Failed to parse comparison results: JSON decode error")
        else:
            # If regex fails, try to parse the entire response as JSON
            try:
                comparison_result = json.loads(comparison_response)
                return {
                    "valid": True,
                    "comparison": comparison_result
                }
            except json.JSONDecodeError:
                logger.error(f"Could not parse comparison response: {comparison_response}")
                raise ValueError("Failed to parse comparison results")
            
    except Exception as e:
        logger.error(f"Error comparing contents: {e}")
        raise RuntimeError(f"Content comparison failed: {e}") from e
