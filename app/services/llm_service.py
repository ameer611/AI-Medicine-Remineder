"""LLM service — wraps Groq chat/completions API."""
import json
import logging
from groq import AsyncGroq

from app.config import settings
from app.schemas.medication import LLMPrescriptionResponse, MedicationLLM

logger = logging.getLogger(__name__)

# Initialize Async Client
client = AsyncGroq(api_key=settings.GROQ_API_KEY)

# We extract the JSON schema from your Pydantic model to tell Groq exactly what we want
JSON_SCHEMA = json.dumps(LLMPrescriptionResponse.model_json_schema(), indent=2)

SYSTEM_PROMPT = f"""You are a clinical pharmacist assistant.
Extract all medications from the prescription text.
You MUST return a JSON object that matches this schema:
{JSON_SCHEMA}

Rules:
- dosage_per_day must be an integer between 1 and 4
- timing must be one of: morning, afternoon, evening, custom
- duration_in_days must be an integer or null
- notes should reflect meal instructions or null"""

class LLMError(Exception):
    pass

async def parse_prescription(text: str) -> list[MedicationLLM]:
    """Call Groq LLM with prescription text using JSON mode."""
    try:
        chat_completion = await client.chat.completions.create(
            # Using Llama 3.3 70B for high reasoning accuracy, 
            # or llama-3.1-8b-instant for maximum speed.
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Prescription text:\n{text}"},
            ],
            temperature=0.1,
            # Enable JSON mode
            response_format={"type": "json_object"},
        )

        content = chat_completion.choices[0].message.content
        if not content:
            raise LLMError("Groq returned an empty response.")

        # Parse and validate with Pydantic
        parsed = LLMPrescriptionResponse.model_validate_json(content)
        
        logger.info("Groq parsed %d medication(s) successfully", len(parsed.medications))
        return parsed.medications

    except Exception as exc:
        logger.error("Groq API Error: %s", exc)
        raise LLMError(f"Failed to process prescription with Groq: {str(exc)}")