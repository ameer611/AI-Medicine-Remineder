"""Shared helper — builds a medication card message."""
from typing import Any


def medication_card(med: dict[str, Any], index: int, total: int) -> str:
    notes = med.get("notes") or "—"
    duration = f"{med['duration_in_days']} days" if med.get("duration_in_days") else "Not set"
    suggested_times = med.get("suggested_times") or []
    suggested_text = ", ".join(suggested_times) if suggested_times else "—"
    reasoning = med.get("timing_reasoning") or "—"
    return (
        f"💊 <b>Medication {index + 1} of {total}</b>\n\n"
        f"<b>Name:</b> {med['name']}\n"
        f"<b>Dosage per day:</b> {med['dosage_per_day']}\n"
        f"<b>Timing:</b> {med.get('timing', 'custom')}\n"
        f"<b>Suggested times:</b> {suggested_text}\n"
        f"<b>Timing reasoning:</b> {reasoning}\n"
        f"<b>Duration:</b> {duration}\n"
        f"<b>Notes:</b> {notes}"
    )
