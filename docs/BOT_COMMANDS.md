# Bot Commands & FSM Reference

Complete reference for Telegram bot commands, FSM state machine, handlers, keyboards, and user workflows.

**Table of Contents**
- [Quick Command Reference](#quick-command-reference)
- [FSM State Machine](#fsm-state-machine)
- [Commands & Handlers](#commands--handlers)
- [Keyboards & Buttons](#keyboards--buttons)
- [User Workflows](#user-workflows)
- [Developer Reference](#developer-reference)

---

## Quick Command Reference

| Command | Handler | Purpose |
|---------|---------|---------|
| `/start` | [start.py](../bot/handlers/start.py) | Welcome & show main menu |
| `/my_medications` | [my_medications.py](../bot/handlers/my_medications.py) | View all active medications |

**Main Menu Buttons:**
- 📸 Scan Prescription
- ⌨️ Add Manually
- 📋 View My Schedules

---

## FSM State Machine

The bot uses Aiogram's **Finite State Machine** to guide users through medication entry. There are 8 states total.

### **State Diagram**

```
                    ┌─ waiting_for_entry_method ◄─────────────────┐
                    │  (Main menu: Scan/Manual/View)               │
                    │                                               │
        ┌───────────▼──────────────┬───────────────────┐            │
        │                          │                   │            │
        ▼                          ▼                   ▼            │
  waiting_for_image         Manual Entry         View Schedules    │
  (Scan prescription)       (Set up empty med)   (Display only)    │
        │                          │                   │            │
        │                          │                   │            │
        ▼                          ▼                   │            │
  confirming_medication ◄────────────────┐            │            │
  (Review medication)                    │            │            │
        │                                 │            │            │
    ┌───┴──────────┬─────────────────────┘            │            │
    │              │                                   │            │
    ▼              ▼                                   │            │
✓ Confirm    Edit                                     │            │
    │          │                                      │            │
    │          ▼                                      │            │
    │      editing_field_choice                       │            │
    │      (Pick: name/dosage/timing/notes/duration) │            │
    │          │                                      │            │
    │          ▼                                      │            │
    │      editing_field_value                        │            │
    │      (Enter new value)                          │            │
    │          │                                      │            │
    │          └────────────┬─────────────────────────┘            │
    │                       │ (Return to confirming_medication)     │
    │                       │                                       │
    ▼                       ▼                                       │
selecting_times ◄────────────────────────────┐                    │
(Choose HH:MM times)                         │                    │
    │                                        │                    │
    ▼                                        │                    │
selecting_reminder_offset                     │                    │
(Choose: 1, 5, 15, 30 mins)                   │                    │
    │                                        │                    │
    ▼                                        │                    │
selecting_duration                            │                    │
(Choose: 1, 7, 14, 30 days)                   │                    │
    │                                        │                    │
    ▼                                        │                    │
✅ SAVE & CLEAR                              │                    │
(Medication persisted, APScheduler jobs)     │                    │
    │                                        │                    │
    └────────────────────────────────────────┘                    │
                    │                                               │
                    └───────────────────────────────────────────────┘
                    Return to waiting_for_entry_method
```

### **State Descriptions**

| State | Handler | Purpose | Transitions |
|-------|---------|---------|------------|
| `waiting_for_entry_method` | [start.py](../bot/handlers/start.py) | Show main menu | → `waiting_for_image` or Manual → `confirming_medication` |
| `waiting_for_image` | [image.py](../bot/handlers/image.py) | Await prescription photo upload | Photo received → `/ocr` → `/parse` → `confirming_medication` |
| `confirming_medication` | [confirm.py](../bot/handlers/confirm.py) | Display parsed medication, ask confirm/edit | Edit → `editing_field_choice`, Confirm → `selecting_times` |
| `editing_field_choice` | [edit.py](../bot/handlers/edit.py) | Ask which field to edit | Choice → `editing_field_value` |
| `editing_field_value` | [edit.py](../bot/handlers/edit.py) | Accept new field value | Value received → `confirming_medication` |
| `selecting_times` | [times.py](../bot/handlers/times.py) | Grid of times 08:00-22:00, select N times per dosage | Times selected → `selecting_reminder_offset` |
| `selecting_reminder_offset` | [reminder.py](../bot/handlers/reminder.py) | Choose early reminder minutes (1, 5, 15, 30) | Offset selected → `selecting_duration` |
| `selecting_duration` | [reminder.py](../bot/handlers/reminder.py) | Choose how many days (1, 7, 14, 30) | Duration selected → Save & Clear → `waiting_for_entry_method` |

---

## Commands & Handlers

### **1. `/start` — Initialize or Welcome**

**Handler File:** [bot/handlers/start.py](../bot/handlers/start.py)

**Triggered By:**
- User types `/start` command
- User clicks "Return to Menu"

**Behavior:**
```
1. Clear any existing FSM state
2. Send welcome message + main menu keyboard
3. Set state: waiting_for_entry_method
```

**Message:**
```
👋 Welcome to the Smart Prescription Reminder Bot!

How would you like to add your medication?

Button Options:
• 📸 Scan Prescription
• ⌨️ Add Manually
• 📋 View My Schedules
```

---

### **2. `/my_medications` — View Active Schedules**

**Handler File:** [bot/handlers/my_medications.py](../bot/handlers/my_medications.py)

**Triggered By:**
- User types `/my_medications` command
- User clicks "📋 View My Schedules" button

**Behavior:**
```
1. Call GET /medications/{telegram_id}/active via FastAPI
2. Format medications list (name, dosage_per_day, times, offsets)
3. Send formatted message to user
```

**Example Output:**
```
📋 Your Active Medications:

1️⃣ Aspirin 500mg
   Doses: 2 times daily
   Times: 08:00, 20:00
   Reminder: 5 minutes before

2️⃣ Vitamin D
   Doses: 1 time daily
   Times: 09:00
   Reminder: 15 minutes before
```

---

### **3. Image Handler — Process Prescription Photo**

**Handler File:** [bot/handlers/image.py](../bot/handlers/image.py)

**Triggered By:**
- User sends a photo when in `waiting_for_image` state

**Behavior:**
```
1. Download photo from Telegram
2. Call POST /ocr with image bytes
3. Receive OCR text from API
4. Display OCR text to user
5. Ask "Does this look correct?" with Yes/No buttons
6. If Yes, call POST /parse with text
7. Receive structured medications from LLM
8. Set state: confirming_medication
9. Display first medication
```

---

### **4. Confirm Handler — Approve or Edit Medication**

**Handler File:** [bot/handlers/confirm.py](../bot/handlers/confirm.py)

**State:** `confirming_medication`

**Buttons:**
- ✅ Confirm (→ `selecting_times`)
- ✏️ Edit (→ `editing_field_choice`)
- ⏭️ Next (if multiple medications) (→ next med or save)
- ← Back (→ wait for new input)

**Behavior:**
```
1. Display medication card:
   • Name
   • Dosage per day
   • Notes (if any)
   • Duration estimate
2. Await button press
   - Confirm: → selecting_times
   - Edit: → editing_field_choice
```

---

### **5. Edit Handler — Modify Medication Fields**

**Handler File:** [bot/handlers/edit.py](../bot/handlers/edit.py)

**States:**
- `editing_field_choice` — Choose field
- `editing_field_value` — Enter new value

**Editable Fields:**
- Name
- Dosage per day (1-4)
- Timing (morning/afternoon/evening/custom)
- Notes
- Duration (estimated from LLM)

**Behavior:**
```
editing_field_choice:
  1. Show button grid with field options
  2. User selects one field
  3. Set state: editing_field_value

editing_field_value:
  1. Ask for new value (context-specific)
     • Name: text input
     • Dosage: 1, 2, 3, 4 buttons
     • Timing: morning/afternoon/evening/custom buttons
     • Notes: text input
     • Duration: 1, 7, 14, 30 days buttons
  2. Receive value
  3. Update FSM state data
  4. Return to confirming_medication
```

---

### **6. Times Handler — Select Daily Times**

**Handler File:** [bot/handlers/times.py](../bot/handlers/times.py)

**State:** `selecting_times`

**Display:**
```
Time Grid (08:00 - 22:00, 30-min intervals):

08:00  08:30  09:00  09:30  10:00
10:30  11:00  11:30  12:00  12:30
13:00  13:30  14:00  14:30  15:00
15:30  16:00  16:30  17:00  17:30
18:00  18:30  19:00  19:30  20:00
20:30  21:00  21:30  22:00

[✅ Confirm Times]  [← Back]
```

**Behavior:**
```
1. Display time grid from 08:00 to 22:00 (30-min intervals)
2. User clicks N times (where N = dosage_per_day)
3. Selected times appear with checkmark
4. Once N times selected, show "✅ Confirm Times" button
5. User confirms → selecting_reminder_offset
```

---

### **7. Reminder Handler — Offset & Duration**

**Handler File:** [bot/handlers/reminder.py](../bot/handlers/reminder.py)

**State 1: `selecting_reminder_offset`**

**Display:**
```
When should we remind you?

[ 1 min ]  [ 5 min ]  [ 15 min ]  [ 30 min ]

[← Back]
```

**Behavior:**
```
1. User selects offset (1, 5, 15, or 30 minutes)
2. Store in FSM state
3. Set state: selecting_duration
```

**State 2: `selecting_duration`**

**Display:**
```
How long should we remind you for?

[ 1 day ]  [ 7 days ]  [ 14 days ]  [ 30 days ]

[← Back]
```

**Behavior:**
```
1. User selects duration (1, 7, 14, or 30 days)
2. Store in FSM state
3. Call POST /medications with all collected data
4. API saves medication + creates APScheduler jobs
5. Clear FSM state
6. Display success message
7. Return to waiting_for_entry_method
```

---

## Keyboards & Buttons

### **Main Menu Keyboard** (Reply Keyboard)

**Location:** [bot/keyboards.py](../bot/keyboards.py)

```python
def main_menu_keyboard():
    """ReplyKeyboard with 3 main options."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📸 Scan Prescription")],
            [KeyboardButton(text="⌨️ Add Manually")],
            [KeyboardButton(text="📋 View My Schedules")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
```

### **Confirm Buttons** (Inline Keyboard)

```python
def confirm_keyboard():
    """InlineKeyboard for confirming medication."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirm", callback_data="confirm"),
                InlineKeyboardButton(text="✏️ Edit", callback_data="edit")
            ],
            [InlineKeyboardButton(text="← Back", callback_data="back")]
        ]
    )
```

### **Edit Field Selection** (Inline Keyboard)

```python
def edit_field_keyboard():
    """InlineKeyboard for selecting which field to edit."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Name", callback_data="edit_name")],
            [InlineKeyboardButton(text="Dosage", callback_data="edit_dosage")],
            [InlineKeyboardButton(text="Timing", callback_data="edit_timing")],
            [InlineKeyboardButton(text="Notes", callback_data="edit_notes")],
            [InlineKeyboardButton(text="Duration", callback_data="edit_duration")],
            [InlineKeyboardButton(text="← Back", callback_data="back")]
        ]
    )
```

---

## User Workflows

### **Workflow 1: Scan Prescription**

```
User                              Bot                               API
 │                                 │                                 │
 ├─ Tap "/start"                  │                                 │
 │                                ├─ Send main menu                 │
 │                                │                                 │
 ├─ Tap "📸 Scan Prescription"    │                                 │
 │                                ├─ Request image                  │
 │                                │                                 │
 ├─ Send prescription image       │                                 │
 │                                ├──────────────────────┐          │
 │                                │ POST /ocr            │          │
 │                                ├─ Extract text ────────────────┤
 │                                │◄──────────────────────          │
 │                                ├─ Show extracted text            │
 │                                │   "Does this look right?"       │
 │                                │                                 │
 ├─ Tap "Yes"                     │                                 │
 │                                ├──────────────────────┐          │
 │                                │ POST /parse          │          │
 │                                ├─ Parse text ──────────────────┤
 │                                │◄──────────────────────          │
 │                                ├─ Display Medication 1          │
 │                                │   "Aspirin 500mg, 2x daily"    │
 │                                │   [✅ Confirm] [✏️ Edit]       │
 │                                │                                 │
 ├─ Make edits (optional)         │                                 │
 │   ├─ Tap "✏️ Edit"             │                                 │
 │   ├─ Select "Dosage"           ├─ Ask for new dosage            │
 │   ├─ Select "3"                ├─ Update state                  │
 │   └─ Return to confirm         │                                 │
 │                                │                                 │
 ├─ Tap "✅ Confirm"              │                                 │
 │                                ├─ Store in state                │
 │                                ├─ Ask to select times           │
 │                                │   "When to take? (3 times)"    │
 │                                │                                 │
 ├─ Select times:                 │                                 │
 │   08:00, 14:00, 20:00          ├─ Store times                   │
 │                                ├─ "How early reminder?"         │
 │                                │   [5 min] [15 min] [30 min]    │
 │                                │                                 │
 ├─ Tap "5 min"                   ├─ Store offset                  │
 │                                ├─ "For how many days?"          │
 │                                │   [1 day] [7 days] [30 days]   │
 │                                │                                 │
 ├─ Tap "7 days"                  ├──────────────────────┐          │
 │                                │ POST /medications   │          │
 │                                ├─ Save & schedule ────────────┤
 │                                │◄──────────────────────          │
 │                                ├─ "✅ Medication saved!"        │
 │                                ├─ APScheduler jobs created      │
 │                                │                                 │
 └─ Reminders start tomorrow      └─ Daily at 07:55, 08:00,       └─ Send daily reminders
   at 07:55, 08:00, 13:55,          13:55, 14:00, 19:55, 20:00      via Telegram API
   14:00, 19:55, 20:00
```

### **Workflow 2: Add Manually**

```
User                   Bot
 │                     │
 ├─ Tap "/start"       │
 │                    ├─ Send main menu
 │                     │
 ├─ Tap "⌨️ + Manual" │
 │                    ├─ Show empty template
 │                     │ [✅ Confirm] [✏️ Edit]
 │                     │
 ├─ Tap "✏️ Edit"     │
 │                    ├─ Ask which field?
 │                     │
 ├─ Tap "Name"        │
 │                    ├─ Ask for name?
 │                     │
 ├─ Type "Aspirin"   │
 │                    ├─ Update, return to confirm
 │                     │
 ├─ Tap "✏️ Edit"     │
 │                    ├─ Ask which field?
 │                     │
 ├─ Tap "Dosage"      │
 │                    ├─ [1] [2] [3] [4]
 │                     │
 ├─ Tap "2"           │
 │                    ├─ Update, return to confirm
 │                     │
 ├─ Tap "✅ Confirm"  │
 │                    ├─ [Proceed to time selection]
 │                     │
 └─ [Same as Workflow 1 from times onward]
```

### **Workflow 3: View Schedules**

```
User                   Bot                      API
 │                     │                         │
 ├─ Tap "/my_meds"    │                         │
 │                    ├────────────────────────┤│
 │                    │ GET /medications/{id}  ││
 │                    │◄─────────────────────────┤
 │                    ├─ Format list            │
 │                    ├─ Send:                  │
 │                    │ "1️⃣ Aspirin 500mg      │
 │                    │  📍 2x daily             │
 │                    │  ⏰ 08:00, 20:00"      │
 │                    │                         │
 └─ View displayed    └─ (Read-only display)   └─
```

---

## Developer Reference

### **Handler File Structure**

Each handler file contains:

1. **Router initialization**
   ```python
   from aiogram import Router
   router = Router()
   ```

2. **Message/Callback handlers decorated with @router.**
   - `@router.message()` — Handle text messages, commands, media
   - `@router.callback_query()` — Handle button clicks

3. **State management via FSMContext**
   ```python
   async def handler(message: Message, state: FSMContext):
       data = await state.get_data()
       await state.update_data(key=value)
       await state.set_state(NewState)
   ```

### **Adding a New Command**

1. Create a new file in `bot/handlers/`:
   ```python
   # bot/handlers/my_command.py
   from aiogram import Router, F
   from aiogram.filters import CommandStart
   from aiogram.fsm.context import FSMContext
   from aiogram.types import Message
   
   router = Router()
   
   @router.message(F.text == "/my_command")
   async def my_command_handler(message: Message) -> None:
       await message.answer("Response")
   ```

2. Register in `run_bot.py`:
   ```python
   from bot.handlers import my_command
   
   dp.include_router(my_command.router)
   ```

### **Adding a New State**

1. Add to `bot/states.py`:
   ```python
   class PrescriptionFlow(StatesGroup):
       my_new_state = State()
   ```

2. Use in handlers:
   ```python
   await state.set_state(PrescriptionFlow.my_new_state)
   ```

### **Key Imports**

```python
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
```

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) — Bot component and data flows
- [API_REFERENCE.md](API_REFERENCE.md) — Endpoints the bot calls
- [USER_GUIDE.md](USER_GUIDE.md) — From end-user perspective
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — Extending bot functionality

---

**Last Updated:** April 2026  
**Status:** Complete
