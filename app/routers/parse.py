"""POST /parse — accepts prescription text and returns structured medications JSON."""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.medication import MedicationLLM
from app.services.llm_service import LLMError, parse_prescription

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/parse", tags=["Parse"])


class ParseRequest(BaseModel):
    text: str


class ParseResponse(BaseModel):
    medications: list[MedicationLLM]


@router.post("", response_model=ParseResponse)
async def parse_endpoint(body: ParseRequest) -> ParseResponse:
    """Parse raw prescription text via Cerebras LLM and return structured medications."""
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")

    try:
        medications = await parse_prescription(body.text)
    except LLMError as exc:
        logger.error("LLM parse failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ParseResponse(medications=medications)
