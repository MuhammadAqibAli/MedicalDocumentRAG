import logging
from api.services.llm_engine import get_llm_instance # Reuse or use a dedicated smaller model
from langchain.prompts import PromptTemplate
logger = logging.getLogger(__name__)

# Use a smaller/faster model for validation if possible, or reuse a main one
VALIDATION_MODEL_NAME = "phi-3-mini-instruct" # Example: Use Mistral for validation

VALIDATION_PROMPT_TEMPLATE = """
You are an expert reviewer for New Zealand healthcare documents. Evaluate the following generated text based on the criteria below. Respond ONLY with a JSON object containing your assessment. Do not add any introductory text or explanation outside the JSON.

CRITERIA:
1.  **Consistency:** Are there internal contradictions or logically inconsistent statements? (Boolean: true/false)
2.  **Clinical Relevance:** Is the content relevant and appropriate for a New Zealand healthcare setting? (Boolean: true/false)
3.  **Language Tone:** Is the language formal, concise, and medically appropriate for the likely document type? (Boolean: true/false)
4.  **Potential Issues:** Briefly list any specific concerns like lack of specificity, potential regulatory conflicts (based on general knowledge), or confusing language. (List of strings, max 3 items)

TEXT TO EVALUATE:
--- START TEXT ---
{generated_text}
--- END TEXT ---

YOUR JSON RESPONSE:
"""

def validate_generated_output(generated_text: str) -> dict:
    """
    Uses an LLM to validate the generated content against predefined criteria.
    Returns a dictionary with validation results.
    """
    logger.info(f"Starting validation for generated text (length: {len(generated_text)})...")
    try:
        validator_llm = get_llm_instance(VALIDATION_MODEL_NAME) # Or configure a dedicated validator LLM
    except Exception as e:
        logger.error(f"Could not initialize validation LLM ({VALIDATION_MODEL_NAME}): {e}")
        return {"error": "Validation LLM unavailable", "details": str(e)}

    prompt = PromptTemplate(template=VALIDATION_PROMPT_TEMPLATE, input_variables=["generated_text"])
    formatted_prompt = prompt.format(generated_text=generated_text)
    
    try:
        # Use the formatted string prompt directly instead of a dict
        response = validator_llm.invoke(formatted_prompt)

        # Clean up response and parse JSON
        if isinstance(response, dict) and 'text' in response: # Adjust if using LLMChain
            raw_json = response['text'].strip()
        elif isinstance(response, str):
            raw_json = response.strip()
        else:
             logger.error(f"Unexpected validation LLM response format: {type(response)} - {response}")
             return {"error": "Unexpected validation response format"}

        # Find the JSON part (sometimes models add extra text)
        json_start = raw_json.find('{')
        json_end = raw_json.rfind('}')
        if json_start != -1 and json_end != -1:
            json_str = raw_json[json_start:json_end+1]
            import json
            try:
                validation_result = json.loads(json_str)
                logger.info("Validation successful.")
                return validation_result
            except json.JSONDecodeError as json_e:
                logger.error(f"Failed to parse validation JSON response: {json_e}\nRaw response: {raw_json}")
                return {"error": "Failed to parse validation JSON", "raw_response": raw_json}
        else:
            logger.error(f"Could not find valid JSON in validation response: {raw_json}")
            return {"error": "No valid JSON found in validation response", "raw_response": raw_json}

    except Exception as e:
        logger.error(f"Validation LLM invocation failed: {e}")
        return {"error": "Validation process failed", "details": str(e)}
