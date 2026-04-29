"""OCR service — Gemini Vision OCR with multilingual post‑processing."""

import asyncio
import base64
import logging
import re
from typing import Final

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OCRError(Exception):
    """Raised when OCR fails or returns unusable text."""


GEMINI_MODELS: Final[tuple[str, ...]] = ("gemini-2.5-flash", "gemini-1.5-flash")
GEMINI_ENDPOINT_TMPL: Final[str] = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
)

NOISE_RE = re.compile(r"\s+")

# Normalize common medication frequency phrases across Uzbek/Russian variants.
# Target token `kuniga` is used because it is already expected/handled downstream by the LLM prompt.
NORMALIZATION_MAP: Final[dict[str, str]] = {
    # Uzbek variants for "per day"
    "kuniga": "kuniga",
    "kuniga ": "kuniga ",
    "кунга": "kuniga",
    "кунiга": "kuniga",  # possible mixed-script OCR artifacts
    "кунiga": "kuniga",
    "кунега": "kuniga",
    "кунега ": "kuniga ",
    # Russian variants for "per day"
    "раз в день": "kuniga",
    "в день": "kuniga",
    "р/д": "kuniga",
}


def _normalize_text(raw: str) -> str:
    """Basic OCR post‑processing and language normalization."""
    if not raw:
        return ""

    text = raw.replace("\u00a0", " ")  # non-breaking space
    text = NOISE_RE.sub(" ", text).strip()
    if not text:
        return ""

    lowered = text.lower()
    for src, dst in NORMALIZATION_MAP.items():
        lowered = lowered.replace(src, dst)

    return lowered


def _infer_mime_type(filename: str) -> str:
    lower = (filename or "").lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".webp"):
        return "image/webp"
    # Bot currently sends "photo.jpg" with mime image/jpeg.
    return "image/jpeg"


async def _extract_text_with_ocr_space(image_bytes: bytes, filename: str) -> str:
    """Fallback OCR provider using OCR.space API."""
    if not settings.OCR_API_KEY:
        raise OCRError("OCR_API_KEY is not configured")

    endpoint = "https://api.ocr.space/parse/image"
    payload = {
        "apikey": settings.OCR_API_KEY,
        "language": "eng",
        "isOverlayRequired": "false",
        "detectOrientation": "true",
        "scale": "true",
        "OCREngine": "2",
    }
    files = {"file": (filename, image_bytes, _infer_mime_type(filename))}

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(endpoint, data=payload, files=files)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            body = ""
            try:
                body = exc.response.text[:500]
            except Exception:
                body = "<unavailable>"
            raise OCRError(f"OCR.space HTTP error: {exc} | body={body}") from exc
        except httpx.RequestError as exc:
            raise OCRError(f"OCR.space network error: {exc}") from exc
        except ValueError as exc:
            raise OCRError("OCR.space returned invalid JSON") from exc

    if data.get("IsErroredOnProcessing"):
        msg = data.get("ErrorMessage") or data.get("ErrorDetails") or "Unknown OCR.space processing error"
        if isinstance(msg, list):
            msg = "; ".join(str(m) for m in msg)
        raise OCRError(f"OCR.space processing error: {msg}")

    parsed = data.get("ParsedResults") or []
    texts = [item.get("ParsedText", "") for item in parsed if isinstance(item, dict)]
    raw_text = "\n".join(t for t in texts if t).strip()
    if not raw_text:
        raise OCRError("OCR.space returned no text")

    return raw_text


async def extract_text(image_bytes: bytes, filename: str = "prescription.jpg") -> str:
    """Extract text from an image using Gemini Vision and return cleaned multilingual text."""
    if not settings.GEMINI_API_KEY:
        raise OCRError("GEMINI_API_KEY is not configured")

    b64 = base64.b64encode(image_bytes).decode("ascii")
    mime_type = _infer_mime_type(filename)

    # Ask for plain OCR text only (no JSON, no commentary), because we pass it to the LLM next.
    prompt = (
        "You are an OCR engine. Extract ALL visible text from the provided prescription image. "
        "Preserve original spelling and mixed Uzbek Latin/Cyrillic and Russian where possible. "
        "Return ONLY the extracted text, with line breaks if appropriate. "
        "Do not include any explanations."
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": b64,
                        }
                    },
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 2048,
        },
    }

    raw_text = ""
    gemini_error: Exception | None = None

    last_exc = None
    data = None
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            for model in GEMINI_MODELS:
                endpoint = GEMINI_ENDPOINT_TMPL.format(model=model, api_key=settings.GEMINI_API_KEY)
                for attempt in range(3):
                    try:
                        resp = await client.post(endpoint, json=payload)
                        resp.raise_for_status()
                        data = resp.json()
                        break
                    except httpx.HTTPStatusError as exc:
                        last_exc = exc
                        status = exc.response.status_code
                        if status in (500, 502, 503, 504):
                            logger.warning("Gemini API error %s on attempt %d. Retrying...", status, attempt + 1)
                            await asyncio.sleep(2 ** attempt)
                            continue

                        # Try a fallback model if the current one is not accepted.
                        if status in (400, 404):
                            logger.warning("Gemini model %s rejected request with %s; trying fallback.", model, status)
                            break

                        logger.error("Gemini OCR HTTP error: %s | body=%s", exc, exc.response.text[:500])
                        raise OCRError(f"Gemini OCR service HTTP error: {exc}") from exc
                    except httpx.RequestError as exc:
                        last_exc = exc
                        logger.warning("Gemini API network error %s on attempt %d. Retrying...", exc, attempt + 1)
                        await asyncio.sleep(2 ** attempt)
                        continue
                    except ValueError as exc:
                        logger.error("Gemini OCR returned non-JSON response: %s", exc)
                        raise OCRError("Gemini OCR returned an invalid response") from exc

                if data is not None:
                    break

        if data is None:
            raise OCRError(f"Gemini OCR failed after retries. Last error: {last_exc}")

        candidates = data.get("candidates") or []
        extracted_parts: list[str] = []
        for cand in candidates:
            content = cand.get("content") or {}
            parts = content.get("parts") or []
            for part in parts:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    extracted_parts.append(part["text"])

        raw_text = "\n".join(t for t in extracted_parts if t).strip()
        if not raw_text:
            raise OCRError("Gemini OCR returned no text")
    except OCRError as exc:
        gemini_error = exc
        logger.warning("Gemini OCR failed, trying OCR.space fallback: %s", exc)
        raw_text = await _extract_text_with_ocr_space(image_bytes, filename)

    normalized = _normalize_text(raw_text)
    if not normalized:
        if gemini_error:
            raise OCRError(f"OCR text became empty after normalization (Gemini failed: {gemini_error})")
        raise OCRError("OCR text became empty after normalization")

    logger.info("OCR extracted %d characters (normalized)", len(normalized))
    return normalized
