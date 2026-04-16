"""POST /ocr — accepts an image file and returns extracted text."""
import logging

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.services.ocr_service import OCRError, extract_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post("")
async def ocr_endpoint(file: UploadFile) -> JSONResponse:
    """Accept an image upload, extract text via ocr.space, return plain text."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        text = await extract_text(image_bytes, filename=file.filename or "prescription.jpg")
    except OCRError as exc:
        logger.warning("OCR failed: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return JSONResponse({"text": text})
