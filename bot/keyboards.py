from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📸 Scan Prescription"),
                KeyboardButton(text="⌨️ Add Manually"),
            ],
            [
                KeyboardButton(text="📋 View My Schedules"),
            ]
        ],
        resize_keyboard=True
    )


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirm", callback_data="confirm"),
                InlineKeyboardButton(text="✏️ Edit", callback_data="edit"),
            ]
        ]
    )


def field_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💊 Name", callback_data="field:name"),
                InlineKeyboardButton(text="📊 Dosage", callback_data="field:dosage"),
            ],
            [
                InlineKeyboardButton(text="🕐 Timing", callback_data="field:timing"),
                InlineKeyboardButton(text="📝 Notes", callback_data="field:notes"),
            ],
            [
                InlineKeyboardButton(text="📅 Duration", callback_data="field:duration"),
            ],
        ]
    )


def timing_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌅 Morning", callback_data="timing:morning"),
                InlineKeyboardButton(text="☀️ Afternoon", callback_data="timing:afternoon"),
            ],
            [
                InlineKeyboardButton(text="🌙 Evening", callback_data="timing:evening"),
                InlineKeyboardButton(text="⚙️ Custom", callback_data="timing:custom"),
            ],
        ]
    )


def times_keyboard(selected: list[str], required: int) -> InlineKeyboardMarkup:
    """Grid of 08:00–22:00 (1-hour steps). Selected times are marked ✓."""
    hours = [f"{h:02d}:00" for h in range(8, 23)]
    rows: list[list[InlineKeyboardButton]] = []

    row: list[InlineKeyboardButton] = []
    for t in hours:
        label = f"✓ {t}" if t in selected else t
        row.append(InlineKeyboardButton(text=label, callback_data=f"time:{t}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    # Other row
    rows.append([InlineKeyboardButton(text="🕐 Other (manual)", callback_data="time:other")])

    # Done only active when count matches
    done_label = f"✅ Done ({len(selected)}/{required})"
    done_cb = "time:done" if len(selected) == required else "time:not_ready"
    rows.append([InlineKeyboardButton(text=done_label, callback_data=done_cb)])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def offset_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1 min before", callback_data="offset:1"),
                InlineKeyboardButton(text="5 min before", callback_data="offset:5"),
            ],
            [
                InlineKeyboardButton(text="10 min before", callback_data="offset:10"),
                InlineKeyboardButton(text="30 min before", callback_data="offset:30"),
            ],
        ]
    )


def duration_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="3 days", callback_data="duration:3"),
                InlineKeyboardButton(text="5 days", callback_data="duration:5"),
                InlineKeyboardButton(text="7 days", callback_data="duration:7"),
            ],
            [
                InlineKeyboardButton(text="14 days", callback_data="duration:14"),
                InlineKeyboardButton(text="30 days", callback_data="duration:30"),
            ],
            [
                InlineKeyboardButton(text="✏️ Enter manually", callback_data="duration:other"),
            ],
        ]
    )


def view_schedules_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 View My Schedules", callback_data="view_my_medications"),
            ]
        ]
    )


def entry_method_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📸 Scan Prescription", callback_data="entry_method:image"),
                InlineKeyboardButton(text="⌨️ Add Manually", callback_data="entry_method:manual"),
            ],
            [
                InlineKeyboardButton(text="📋 View My Schedules", callback_data="view_my_medications"),
            ]
        ]
    )


def request_contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Share phone number", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def supervisor_selection_keyboard(supervisors: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for supervisor in supervisors:
        rows.append([
            InlineKeyboardButton(
                text=supervisor.get("full_name") or f"Supervisor {supervisor.get('id')}",
                callback_data=f"supervisor:{supervisor.get('id')}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_or_customize_times_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Use these times", callback_data="times:use_suggested"),
                InlineKeyboardButton(text="✏️ Customize", callback_data="times:customize"),
            ]
        ]
    )


def intake_action_keyboard(medication_id: int, schedule_id: int, date: str, time: str) -> InlineKeyboardMarkup:
    def _cb(action: str) -> str:
        return f"intake_{action}:{medication_id}:{schedule_id}:{date}:{time}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Consumed", callback_data=_cb("consumed")),
                InlineKeyboardButton(text="❌ Not consumed", callback_data=_cb("not_consumed")),
                InlineKeyboardButton(text="😟 Feeling bad", callback_data=_cb("felt_bad")),
            ]
        ]
    )
