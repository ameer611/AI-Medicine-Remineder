from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from bot.states import PrescriptionFlow
from bot.keyboards import main_menu_keyboard
from bot.handlers.utils import medication_card
from bot.keyboards import confirm_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "👋 Welcome to the Smart Prescription Reminder Bot!\n\n"
        "How would you like to add your medication?",
        reply_markup=main_menu_keyboard()
    )


@router.message(F.text == "📸 Scan Prescription")
async def on_scan_prescription(message: Message, state: FSMContext) -> None:
    await state.set_state(PrescriptionFlow.waiting_for_image)
    await message.answer(
        "📸 Please send me a photo of your prescription.",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(F.text == "⌨️ Add Manually")
async def on_add_manually(message: Message, state: FSMContext) -> None:
    # Manual entry — initialize empty med so user can edit it
    medications = [
        {
            "name": "New Medication (Click Edit to change)",
            "dosage_per_day": 1,
            "timing": "custom",
            "duration_in_days": None,
            "notes": None,
        }
    ]
    await state.update_data(medications=medications, current_index=0)
    await state.set_state(PrescriptionFlow.confirming_medication)
    
    await message.answer(
        "⌨️ <b>Manual Entry Mode</b>\n\n" +
        medication_card(medications[0], 0, 1),
        reply_markup=confirm_keyboard()
    )


@router.message(F.text == "📋 View My Schedules")
async def on_view_schedules(message: Message) -> None:
    from bot.handlers.my_medications import cmd_my_medications
    await cmd_my_medications(message)
