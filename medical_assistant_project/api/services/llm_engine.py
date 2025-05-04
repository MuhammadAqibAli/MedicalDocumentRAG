import os
from langchain_huggingface import HuggingFaceEndpoint
from langchain_community.llms import LlamaCpp # For local GGUF models
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import logging

logger = logging.getLogger(__name__)

# --- Model Configuration ---
# Define available models. Use environment variables for flexibility.
AVAILABLE_MODELS = {
    "llama3-8b-instruct": { # Example using Hugging Face Inference API
        "type": "hf_endpoint",
        "repo_id": "meta-llama/Meta-Llama-3-8B-Instruct", # Or other suitable repo
        "task": "text-generation",
    },
    "mistral-7b-instruct": {
        "type": "hf_endpoint",
        "repo_id": "mistralai/Mistral-7B-Instruct-v0.2",
        "task": "text-generation",
    },
    "phi-3-mini-instruct": {
        "type": "hf_endpoint",
        "repo_id": "microsoft/Phi-3-mini-4k-instruct",
        "task": "text-generation",
    },
    "tinyllama-1.1b-chat": {
        "type": "hf_endpoint",
        "repo_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "task": "text-generation",
    },
    # Add more models like Falcon, OpenHermes via endpoint...
    # --- Optional: Local LlamaCpp Configuration ---
    # "llama3-8b-local": {
    #     "type": "llama_cpp",
    #     "model_path": "/path/to/your/llama-3-8b-instruct.Q4_K_M.gguf", # Path to downloaded GGUF file
    #     "n_gpu_layers": -1, # -1 to use all available layers on GPU, 0 for CPU only
    #     "n_batch": 512,
    #     "n_ctx": 4096, # Context window size
    #     "verbose": True,
    # },
}

# --- Prompt Template ---
# Note: Adjust template based on the specific model's expected input format (e.g., Llama3 uses specific roles)
RAG_PROMPT_TEMPLATE = """
You are a helpful assistant specialized in creating documents compliant with New Zealand healthcare standards and terminology. Your tone should be formal, concise, and medically appropriate.

Generate a {content_type} about the following topic: "{topic}"

Use the following context from internal documents as your primary source:
--- CONTEXT START ---
{context}
--- CONTEXT END ---

If the context is insufficient or irrelevant to the topic, state that you are generating the content based on your general knowledge while maintaining the NZ healthcare style, but mention that internal document context was not applicable.
Generate only the {content_type} content based on the topic and context provided.
"""

FALLBACK_PROMPT_TEMPLATE = """
You are a helpful assistant specialized in creating documents compliant with New Zealand healthcare standards and terminology. Your tone should be formal, concise, and medically appropriate.

Generate a {content_type} about the following topic: "{topic}"

Generate only the {content_type} content based on the topic provided. Rely on your general knowledge of healthcare best practices, adapted for a New Zealand context where possible.
"""

def get_llm_instance(model_name: str):
    """Gets an instance of the specified LLM."""
    if model_name not in AVAILABLE_MODELS:
        raise ValueError(f"Model '{model_name}' is not configured.")

    config = AVAILABLE_MODELS[model_name]
    llm_type = config["type"]

    if llm_type == "hf_endpoint":
        hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        if not hf_token:
            raise ValueError("HUGGINGFACEHUB_API_TOKEN environment variable not set.")
        try:
            llm = HuggingFaceEndpoint(
                repo_id=config["repo_id"],
                task=config.get("task", "text-generation"),
                huggingfacehub_api_token=hf_token,
                temperature=0.7, # Adjust generation parameters
                max_new_tokens=1024,
                # Add other parameters like top_p, top_k, repetition_penalty as needed
            )
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize HuggingFaceEndpoint for {model_name}: {e}")
            raise ConnectionError(f"Could not connect to HuggingFace model {model_name}") from e

    elif llm_type == "llama_cpp":
        try:
            llm = LlamaCpp(
                model_path=config["model_path"],
                n_gpu_layers=config.get("n_gpu_layers", 0),
                n_batch=config.get("n_batch", 512),
                n_ctx=config.get("n_ctx", 2048),
                f16_kv=True, # Enable if supported and desired
                verbose=config.get("verbose", False),
                temperature=0.7,
                max_tokens=1024,
                 # stop=["\nHuman:", "\nObservation:"] # Add model-specific stop sequences if needed
            )
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize LlamaCpp for {model_name}: {e}")
            raise RuntimeError(f"Could not load local model {model_name}") from e

    else:
        raise ValueError(f"Unsupported LLM type: {llm_type}")


def generate_content_with_llm(topic: str, content_type: str, model_name: str, context: str | None = None):
    """
    Generates content using the specified LLM, applying RAG or fallback logic.
    """
    llm = get_llm_instance(model_name)

    if context:
        prompt_template = PromptTemplate(
            template=RAG_PROMPT_TEMPLATE,
            input_variables=["content_type", "topic", "context"]
        )
        chain = LLMChain(llm=llm, prompt=prompt_template)
        input_data = {"content_type": content_type, "topic": topic, "context": context}
    else:
        prompt_template = PromptTemplate(
            template=FALLBACK_PROMPT_TEMPLATE,
            input_variables=["content_type", "topic"]
        )
        chain = LLMChain(llm=llm, prompt=prompt_template)
        input_data = {"content_type": content_type, "topic": topic}

    logger.info(f"Generating content for '{topic}' ({content_type}) using {model_name}. RAG context: {'Yes' if context else 'No'}")

    try:
        # Some models return result in a dict, others directly. Adapt as needed.
        # Check Langchain docs for the specific LLM wrapper you use.
        response = chain.invoke(input_data)

        # Extract the actual text - this key ('text' for LLMChain) might vary!
        if isinstance(response, dict) and 'text' in response:
             generated_text = response['text'].strip()
        elif isinstance(response, str):
             generated_text = response.strip()
        else:
            logger.error(f"Unexpected LLM response format: {type(response)} - {response}")
            raise TypeError("Could not parse LLM response.")

        logger.info(f"Successfully generated content for '{topic}' using {model_name}.")
        return generated_text

    except Exception as e:
        logger.error(f"LLM generation failed for '{topic}' using {model_name}: {e}")
        raise RuntimeError(f"LLM generation failed: {e}") from e