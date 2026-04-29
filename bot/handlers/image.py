"""Image handler — handles photo upload, calls API for OCR + LLM."""
import logging
from io import BytesIO

import httpx
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.utils import medication_card
from bot.keyboards import confirm_keyboard
from bot.states import PrescriptionFlow
from app.config import settings

logger = logging.getLogger(__name__)
router = Router()


@router.message(PrescriptionFlow.waiting_for_image, F.photo)
async def handle_prescription_photo(message: Message, state: FSMContext, bot: Bot) -> None:
    msg = await message.answer("🔄 Processing image with OCR...")
    
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    
    if not downloaded_file:
        await msg.edit_text("❌ Failed to download image. Please try again.")
        return

    image_bytes = downloaded_file.read()

    # Call our internal FastAPI /ocr
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            ocr_resp = await client.post(
                f"{settings.API_BASE_URL}/ocr",
                files={"file": ("photo.jpg", image_bytes, "image/jpeg")},
            )
            ocr_resp.raise_for_status()
            text = ocr_resp.json().get("text", "")
            if not text:
                raise ValueError("Empty OCR text")
        except httpx.HTTPStatusError as exc:
            detail = ""
            try:
                payload = exc.response.json()
                detail = payload.get("detail", "") if isinstance(payload, dict) else ""
            except Exception:
                detail = exc.response.text[:300] if exc.response is not None else ""

            logger.error("OCR API HTTP error: %s | detail=%s", exc, detail)
            await msg.edit_text(
                "❌ Failed to extract text from the image. "
                f"{('Reason: ' + detail) if detail else 'Please try a clearer photo.'}"
            )
            return
        except Exception as exc:
            logger.error("OCR API error: %s", exc)
            await msg.edit_text("❌ Failed to extract text from the image. Please try a clearer photo.")
            return

        await msg.edit_text("🧠 Analyzing prescription with AI...")

        # Call our internal FastAPI /parse
        try:
            parse_resp = await client.post(
                f"{settings.API_BASE_URL}/parse",
                json={"text": text},
            )
            parse_resp.raise_for_status()
            medications = parse_resp.json().get("medications", [])
            if not medications:
                raise ValueError("No medications parsed")
        except Exception as exc:
            logger.error("Parse API error: %s", exc)
            await msg.edit_text("❌ AI failed to understand the prescription. Please manual entry is not supported yet, try another photo.")
            return

    # Store in FSM
    await state.update_data(medications=medications, current_index=0)
    await state.set_state(PrescriptionFlow.confirming_medication)

    # Show first medication
    med = medications[0]
    await msg.edit_text(
        medication_card(med, 0, len(medications)),
        reply_markup=confirm_keyboard(),
    )
