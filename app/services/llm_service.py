"""LLM service — wraps Google Gemini API."""
import logging
import google.generativeai as genai
from google.api_core import retry

from app.config import settings
from app.schemas.medication import LLMPrescriptionResponse, MedicationLLM

logger = logging.getLogger(__name__)

# Configure the SDK
genai.configure(api_key=settings.GOOGLE_API_KEY)

SYSTEM_PROMPT = """You are a clinical pharmacist assistant.
Extract all medications from the prescription text.
Rules:
- dosage_per_day must be between 1 and 4
- timing must be one of: morning, afternoon, evening, custom
- duration_in_days must be the schedule course length in days or null if not told
- notes should reflect meal instructions (e.g. "after meal", "before meal") or null"""

class LLMError(Exception):
    pass

async def parse_prescription(text: str) -> list[MedicationLLM]:
    """Call Google Gemini with prescription text using controlled JSON output."""
    
    # Initialize the model with Response MIME Type constraints
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": LLMPrescriptionResponse, # Gemini uses your Pydantic model directly!
            "temperature": 0.1,
        },
        system_instruction=SYSTEM_PROMPT
    )

    try:
        # Gemini's SDK handles retries internally if configured, 
        # but we'll wrap it for consistency.
        response = await model.generate_content_async(
            f"Prescription text:\n{text}",
            # Use a retry policy for transient network issues
            request_options={'retry': retry.Retry(predicate=retry.if_transient_error)}
        )

        if not response.text:
            raise LLMError("Empty response from Gemini")

        # Validation: Gemini guarantees JSON structure per response_schema
        parsed = LLMPrescriptionResponse.model_validate_json(response.text)
        
        logger.info("Gemini parsed %d medication(s)", len(parsed.medications))
        return parsed.medications

    except Exception as exc:
        logger.error("Gemini API error: %s", exc)
        raise LLMError(f"Failed to parse prescription: {str(exc)}") from exc