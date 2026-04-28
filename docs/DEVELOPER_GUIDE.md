# Developer Guide

Setup, development workflow, codebase patterns, and extending Dori Scheduler.

**Table of Contents**
- [Local Development Setup](#local-development-setup)
- [Project Structure](#project-structure)
- [Coding Patterns & Conventions](#coding-patterns--conventions)
- [Adding a New API Endpoint](#adding-a-new-api-endpoint)
- [Adding a New Bot Handler](#adding-a-new-bot-handler)
- [Adding a New Database Model](#adding-a-new-database-model)
- [Running Tests](#running-tests)
- [Common Tasks](#common-tasks)

---

## Local Development Setup

### **Prerequisites**

- Python 3.10 or later
- MySQL 8.0 or later (or use Docker)
- Git
- pip or conda

### **Step 1: Clone Repository**

```bash
git clone https://github.com/yourusername/dori_scheduler.git
cd dori_scheduler
```

### **Step 2: Create Virtual Environment**

```bash
# Using venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using conda
conda create -n dori python=3.10
conda activate dori
```

### **Step 3: Install Dependencies**

```bash
pip install -r requirements.txt
```

### **Step 4: Configure Environment**

Copy the example config:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_google_gemini_key
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=mysql+aiomysql://root:password@localhost:3306/dori_scheduler
API_BASE_URL=http://localhost:8000
```

### **Step 5: Set Up Database**

**Option A: Use Docker (Recommended)**

```bash
# Start MySQL container
docker run -d \
  --name dori_mysql \
  -e MYSQL_ROOT_PASSWORD=rootsecret \
  -e MYSQL_DATABASE=dori_scheduler \
  -e MYSQL_USER=dori \
  -e MYSQL_PASSWORD=secret \
  -p 3307:3306 \
  mysql:8.0

# Update .env:
# DATABASE_URL=mysql+aiomysql://dori:secret@localhost:3307/dori_scheduler
```

**Option B: Local MySQL**

```bash
# Create database
mysql -u root -p
CREATE DATABASE dori_scheduler;
CREATE USER 'dori'@'localhost' IDENTIFIED BY 'secret';
GRANT ALL PRIVILEGES ON dori_scheduler.* TO 'dori'@'localhost';
FLUSH PRIVILEGES;
```

### **Step 6: Initialize Database**

Create all tables:

```bash
python -c "
import asyncio
from app.database import init_db
asyncio.run(init_db())
"
```

### **Step 7: Run Services**

**Terminal 1: API Server**
```bash
cd /path/to/dori_scheduler
python run_api.py
# Runs on http://localhost:8000
```

**Terminal 2: Bot Server**
```bash
cd /path/to/dori_scheduler
python run_bot.py
# Logs will show "Starting bot polling..."
```

**Verify:**
- API: Open `http://localhost:8000/docs` (Swagger UI)
- Bot: Should show "Starting bot polling..." in terminal
- Send `/start` command in Telegram

---

## Project Structure

```
dori_scheduler/
│
├── 📁 app/                           # FastAPI Backend
│   ├── 📄 main.py                    # FastAPI app initialization, routers
│   ├── 📄 config.py                  # Settings & environment variables
│   ├── 📄 database.py                # SQLAlchemy setup, session factory
│   ├── 📄 logging_config.py          # Logging configuration
│   │
│   ├── 📁 models/                    # SQLAlchemy ORM models
│   │   ├── 📄 user.py                # User model (telegram_id)
│   │   ├── 📄 medication.py          # Medication model
│   │   └── 📄 schedule.py            # Schedule model (times per day)
│   │
│   ├── 📁 repositories/              # Data access layer (DAL)
│   │   ├── 📄 user_repo.py           # UserRepository
│   │   ├── 📄 medication_repo.py     # MedicationRepository
│   │   └── 📄 schedule_repo.py       # ScheduleRepository
│   │
│   ├── 📁 routers/                   # API endpoints
│   │   ├── 📄 ocr.py                 # POST /ocr — Image text extraction
│   │   ├── 📄 parse.py               # POST /parse — LLM parsing
│   │   └── 📄 medications.py         # POST/GET /medications
│   │
│   ├── 📁 schemas/                   # Pydantic validation schemas
│   │   ├── 📄 medication.py          # MedicationCreate, MedicationRead, etc.
│   │   └── 📄 schedule.py            # ScheduleRead
│   │
│   └── 📁 services/                  # Business logic layer
│       ├── 📄 ocr_service.py         # Google Gemini Vision API
│       ├── 📄 llm_service.py         # Groq LLM parsing
│       ├── 📄 medication_service.py  # Medication operations
│       └── 📄 scheduler_service.py   # APScheduler job manager
│
├── 📁 bot/                           # Telegram Bot (Aiogram)
│   ├── 📄 __init__.py
│   ├── 📄 states.py                  # FSM state definitions
│   ├── 📄 keyboards.py               # Inline/reply keyboards
│   │
│   └── 📁 handlers/                  # Message/callback handlers
│       ├── 📄 start.py               # /start command (init, menu)
│       ├── 📄 image.py               # Photo upload & OCR
│       ├── 📄 confirm.py             # Confirm/edit medication
│       ├── 📄 edit.py                # Edit medication fields
│       ├── 📄 times.py               # Select daily times
│       ├── 📄 reminder.py            # Set reminder offset & duration
│       ├── 📄 my_medications.py      # /my_medications command
│       └── 📄 utils.py               # Shared utilities
│
├── 📁 docs/                          # Documentation (this folder)
│   ├── 📄 README.md                  # Documentation hub
│   ├── 📄 ARCHITECTURE.md            # System design
│   ├── 📄 DATABASE.md                # Schema & models
│   ├── 📄 API_REFERENCE.md           # Endpoint docs
│   ├── 📄 BOT_COMMANDS.md            # Bot commands & FSM
│   ├── 📄 USER_GUIDE.md              # End-user guide
│   ├── 📄 DEVELOPER_GUIDE.md         # This file
│   └── 📄 DEPLOYMENT.md              # Production setup
│
├── 📄 run_api.py                     # API startup script
├── 📄 run_bot.py                     # Bot startup script
├── 📄 requirements.txt                # Python dependencies
├── 📄 docker-compose.yml             # Multi-container orchestration
├── 📄 Dockerfile                     # Container build instructions
├── 📄 .env.example                   # Environment template
└── 📄 README.md                      # Project README

```

---

## Coding Patterns & Conventions

### **Async/Await Pattern**

All database queries, API calls, and bot operations use `async`/`await`:

```python
# ✅ Correct
async def get_user_medications(user_id: int) -> list[Medication]:
    user_repo = UserRepository(session)
    meds = await user_repo.get_by_user_id(user_id)
    return meds

# ❌ Wrong (blocking)
def get_user_medications(user_id: int) -> list[Medication]:
    meds = session.query(Medication).filter(...).all()  # Blocks entire app!
```

### **Dependency Injection (FastAPI)**

Use FastAPI's `Depends()` for database sessions:

```python
@router.post("/medications")
async def save_medication(
    body: SaveMedicationRequest,
    session: AsyncSession = Depends(get_db),  # Injected by FastAPI
) -> SaveMedicationResponse:
    # session is AsyncSession, auto-managed
    ...
```

### **Repository Pattern**

Access data through repositories, not direct ORM:

```python
# ✅ Correct
user_repo = UserRepository(session)
user = await user_repo.get_by_telegram_id(123456789)

# ❌ Wrong (tight coupling to ORM)
stmt = select(User).where(User.telegram_id == 123456789)
result = await session.execute(stmt)
user = result.scalar_one_or_none()
```

### **Service Layer**

Services handle business logic; routers delegate:

```python
# ✅ Correct structure
# Router: Accept request, call service
@router.post("/medications")
async def save_medication(body: SaveMedicationRequest, session: AsyncSession):
    response = await medication_service.save_medication_with_schedules(...)
    return response

# Service: Contains logic
# app/services/medication_service.py
async def save_medication_with_schedules(...):
    # Complex logic here
    med = await medication_repo.create(...)
    schedules = [await schedule_repo.create(...) for t in times]
    await scheduler_service.create_jobs(...)
    return med, schedules

# ❌ Wrong (logic in router)
@router.post("/medications")
async def save_medication(body: SaveMedicationRequest, session: AsyncSession):
    # Don't put complex logic here!
    user = ...
    med = ...
    for t in times:
        sched = ...
    # APScheduler code...
```

### **Pydantic Schemas**

Use schemas for validation, not bare dicts:

```python
# ✅ Correct
class MedicationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    dosage_per_day: int = Field(..., ge=1, le=4)
    notes: str | None = None

@router.post("/medications")
async def save_medication(body: SaveMedicationRequest) -> SaveMedicationResponse:
    # body is validated by Pydantic
    ...

# ❌ Wrong (no validation)
@router.post("/medications")
async def save_medication(body: dict) -> dict:
    # body could be anything!
    ...
```

### **Error Handling**

Raise `HTTPException` for API errors:

```python
# ✅ Correct
from fastapi import HTTPException

if not body.times:
    raise HTTPException(status_code=400, detail="At least one time required")

# ❌ Wrong (raw exception)
if not body.times:
    raise ValueError("At least one time required")  # Uncaught!
```

### **Logging**

Use module-level loggers:

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Processing medication %s", med.name)
logger.warning("OCR confidence low: %s", confidence)
logger.error("Database error: %s", exc)
```

---

## Adding a New API Endpoint

### **Example: Add `GET /medications/search`**

**Step 1: Add Router**

Create `app/routers/search_medications.py`:

```python
import logging
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.database import get_db
from app.models import Medication
from app.schemas import MedicationRead

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/medications/search", tags=["Medications"])


@router.get("", response_model=list[MedicationRead])
async def search_medications(
    query: str = Query(..., min_length=1),
    session: AsyncSession = None,
) -> list[MedicationRead]:
    """Search medications by name."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="Search query required")
    
    # Search logic
    stmt = select(Medication).where(
        Medication.name.ilike(f"%{query}%")
    )
    result = await session.execute(stmt)
    medications = result.scalars().all()
    
    logger.info("Search '%s' returned %d results", query, len(medications))
    return medications
```

**Step 2: Register in `app/main.py`**

```python
from app.routers import medications, ocr, parse, search_medications

app.include_router(ocr.router)
app.include_router(parse.router)
app.include_router(medications.router)
app.include_router(search_medications.router)  # Add this
```

**Step 3: Test**

```bash
curl "http://localhost:8000/medications/search?query=aspirin"
```

---

## Adding a New Bot Handler

### **Example: Add `/edit_medication` Command**

**Step 1: Create Handler**

Create `bot/handlers/edit_med.py`:

```python
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.states import PrescriptionFlow
from bot.keyboards import main_menu_keyboard

router = Router()


@router.message(Command("edit_medication"))
async def cmd_edit_medication(message: Message, state: FSMContext) -> None:
    """Edit existing medication (future feature)."""
    await message.answer(
        "📝 Edit Medication\n\n"
        "This feature is coming soon!\n"
        "For now, delete and re-add the medication."
    )
```

**Step 2: Register in `run_bot.py`**

```python
from bot.handlers import start, image, confirm, edit, times, reminder, my_medications, edit_med

# ... in main() function:
dp.include_router(edit_med.router)  # Add this
```

**Step 3: Test**

Send `/edit_medication` in Telegram. Bot should respond.

---

## Adding a New Database Model

### **Example: Add `MedicationHistory` Model**

**Step 1: Create Model**

Create `app/models/history.py`:

```python
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MedicationHistory(Base):
    """Track when users took their medications."""
    __tablename__ = "medication_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    medication_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("medications.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    taken_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    medication: Mapped["Medication"] = relationship("Medication")
    user: Mapped["User"] = relationship("User")
```

**Step 2: Create Repository**

Create `app/repositories/history_repo.py`:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MedicationHistory


class HistoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def record_taken(self, medication_id: int, user_id: int, notes: str | None = None) -> MedicationHistory:
        history = MedicationHistory(
            medication_id=medication_id,
            user_id=user_id,
            notes=notes
        )
        self.session.add(history)
        await self.session.flush()
        return history
    
    async def get_history(self, medication_id: int, limit: int = 30) -> list[MedicationHistory]:
        stmt = select(MedicationHistory).where(
            MedicationHistory.medication_id == medication_id
        ).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
```

**Step 3: Create Pydantic Schema**

Create schema in `app/schemas/history.py`:

```python
from datetime import datetime
from pydantic import BaseModel


class HistoryRead(BaseModel):
    id: int
    medication_id: int
    taken_at: datetime
    notes: str | None
    
    model_config = {"from_attributes": True}
```

**Step 4: Initialize Schema**

Update model imports in `app/models/__init__.py`:

```python
from app.models.user import User
from app.models.medication import Medication
from app.models.schedule import Schedule
from app.models.history import MedicationHistory  # Add this
```

**Step 5: Create Tables**

Run:
```bash
python -c "
import asyncio
from app.database import init_db
asyncio.run(init_db())
"
```

---

## Running Tests

Tests are not yet implemented in this project. To add testing:

### **Setup pytest**

```bash
pip install pytest pytest-asyncio httpx
```

### **Example Test**

Create `tests/test_api.py`:

```python
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    
    assert response.status_code == 200
```

### **Run Tests**

```bash
pytest tests/ -v
```

---

## Common Tasks

### **Check API Documentation**

```bash
# Start API
python run_api.py

# Open in browser
open http://localhost:8000/docs  # macOS
# or navigate manually to that URL
```

Swagger UI shows all endpoints, schemas, and responses.

### **View Database**

**Using MySQL CLI:**
```bash
mysql -u dori -psecret -D dori_scheduler

# View users
SELECT * FROM users;

# View medications for user 1
SELECT * FROM medications WHERE user_id = 1;

# View schedules
SELECT * FROM schedules WHERE medication_id = 1;
```

**Using GUI (optional):**
- Install MySQL Workbench or DataGrip
- Connect to localhost:3307 (Docker) or localhost:3306 (local)
- Browse tables visually

### **Check Logs**

**API logs:**
```
# In run_api.py terminal
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Bot logs:**
```
# In run_bot.py terminal
INFO:root:Starting bot polling...
DEBUG:aiogram.client.session:Request: POST https://api.telegram.org/...
```

### **Debug a State Issue**

Add debug logging to handler:

```python
@router.message(F.text == "Some Button")
async def handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    logger.debug("Current state data: %s", data)
    await state.set_state(NewState)
    logger.debug("Transitioned to: %s", NewState)
```

### **Test an Endpoint with curl**

```bash
# Test /parse
curl -X POST http://localhost:8000/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "Aspirin twice daily for 7 days"}'

# Test GET medications
curl http://localhost:8000/medications/1
```

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) — System design and data flows
- [DATABASE.md](DATABASE.md) — Model structure and relationships
- [API_REFERENCE.md](API_REFERENCE.md) — Endpoint documentation
- [BOT_COMMANDS.md](BOT_COMMANDS.md) — Handler structure
- [DEPLOYMENT.md](DEPLOYMENT.md) — Production setup

---

**Last Updated:** April 2026  
**Status:** Complete
