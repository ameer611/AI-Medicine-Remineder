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
Extract all medications from the prescription text and suggest specific clock times for each dose.
You MUST return a JSON object that matches this schema:
{JSON_SCHEMA}

Important rules:
- `dosage_per_day` must be an integer between 1 and 4.
- `suggested_times` must contain exactly `dosage_per_day` entries, each in HH:MM 24-hour format (e.g. 08:00).
- When notes include meal context (e.g., "after meal", "with food"), prefer meal times (08:00, 13:00, 19:00).
- For instructions like "before sleep" or "at bedtime", choose a late evening time (e.g., 22:00).
- For antibiotics or medications requiring even spacing, distribute times evenly (e.g., 08:00, 16:00, 00:00 for 3x/day if appropriate).
- `timing_reasoning` should be a brief explanation (1-2 sentences) describing why these times were chosen, in the same language as the prescription.
- `duration_in_days` should be an integer when specified, otherwise null.
- `notes` should capture meal-related or other instruction text when present, otherwise null.

Return concise, clinically sensible times and a short reasoning for each medication."""

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