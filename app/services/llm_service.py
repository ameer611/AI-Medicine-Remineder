"""LLM service — wraps Cerebras chat/completions API."""
import json
import logging

import httpx

from app.config import settings
from app.schemas.medication import LLMPrescriptionResponse, MedicationLLM

logger = logging.getLogger(__name__)

CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"
MAX_RETRIES = 3

SYSTEM_PROMPT = """You are a clinical pharmacist assistant.
Extract all medications from the prescription text and return ONLY a JSON object (no markdown, no extra text) in this exact schema:

{
  "medications": [
    {
      "name": "string",
      "dosage_per_day": <integer 1-4>,
      "timing": "<morning|afternoon|evening|custom>",
      "duration_in_days": <integer or null>,
      "notes": "string or null"
    }
  ]
}

Rules:
- dosage_per_day must be between 1 and 4
- timing must be one of: morning, afternoon, evening, custom
- duration_in_days must be the schedule course length in days or null if not told
- notes should reflect meal instructions (e.g. "after meal", "before meal") or null
- Return ONLY valid JSON, no markdown code fences"""


class LLMError(Exception):
    pass


async def parse_prescription(text: str) -> list[MedicationLLM]:
    """Call Cerebras LLM with prescription text. Retries up to MAX_RETRIES on bad JSON."""
    headers = {
        "Authorization": f"Bearer {settings.CEREBRAS_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "llama3.1-8b",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Prescription text:\n{text}"},
        ],
        "temperature": 0.1,
        "max_tokens": 1024,
    }

    last_error: Exception | None = None

    async with httpx.AsyncClient(timeout=60.0) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await client.post(CEREBRAS_URL, headers=headers, json=body)
                response.raise_for_status()
                data = response.json()

                content: str = data["choices"][0]["message"]["content"].strip()
                logger.debug("LLM raw content (attempt %d): %s", attempt, content)

                # Strip accidental markdown fences
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip()

                parsed = LLMPrescriptionResponse.model_validate(json.loads(content))
                logger.info("LLM parsed %d medication(s)", len(parsed.medications))
                return parsed.medications

            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                logger.warning("LLM attempt %d failed to parse JSON: %s", attempt, exc)
                last_error = exc
            except httpx.HTTPStatusError as exc:
                logger.error("LLM HTTP error: %s", exc)
                raise LLMError(f"Cerebras API error: {exc.response.status_code}") from exc

    raise LLMError(f"LLM failed to return valid JSON after {MAX_RETRIES} attempts: {last_error}")
