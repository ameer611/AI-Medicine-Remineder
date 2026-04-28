# Architecture & Design

This document explains the system architecture, component relationships, data flows, and design decisions for Dori Scheduler.

**Table of Contents**
- [System Overview](#system-overview)
- [Architecture Diagram](#architecture-diagram)
- [Component Responsibilities](#component-responsibilities)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Design Decisions](#design-decisions)
- [Async Architecture](#async-architecture)

---

## System Overview

**Dori Scheduler** is a **three-tier microservice** architecture:

1. **Telegram Bot** (Aiogram) — User-facing interface
2. **FastAPI Backend** — REST API for business logic
3. **MySQL Database** — Persistent data storage

External services integrate via APIs:
- **Google Gemini Vision** — Prescription OCR
- **Groq LLM** — Prescription text parsing
- **APScheduler** — Task scheduling for reminders

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        TELEGRAM USERS                           │
│                    (Telegram Client App)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                  Telegram Bot API
                   (HTTPS Polling)
                         │
        ┌────────────────┴────────────────┐
        │                                 │
    ┌───▼─────────────────┐      ┌────────▼──────────────┐
    │  TELEGRAM BOT       │      │  FASTAPI BACKEND      │
    │  (run_bot.py)       │◄────►│  (run_api.py)         │
    │                     │ httpx│  Port 8000            │
    │ • Aiogram 3.x       │      │                       │
    │ • FSM Handler       │      │ Routers:              │
    │ • 7 Router Groups   │      │ • POST /ocr           │
    │ • Keyboards         │      │ • POST /parse         │
    │ • APScheduler       │      │ • POST /medications   │
    │   (reminders)       │      │ • GET /medications/{id}
    │                     │      │                       │
    └──────────┬──────────┘      └──────────┬────────────┘
               │                           │
               │                    SQLAlchemy ORM
               │                    (async)
               │                           │
               │              ┌────────────▼─────────┐
               │              │   MYSQL 8.0 DATABASE │
               │              │                      │
               │              │ Tables:              │
               │              │ • users              │
               │              │ • medications        │
               │              │ • schedules          │
               │              │                      │
               │              │ Relationships:       │
               │              │ User → Medications   │
               │              │   → Schedules        │
               │              └──────────────────────┘
               │
               └─────────────────────────────────────────┐
                                                         │
        ┌────────────────────────────────────────────────▼────────┐
        │         EXTERNAL AI/OCR APIs                             │
        ├──────────────────────────────────────────────────────────┤
        │                                                           │
        │  • Google Gemini Vision API                              │
        │    (Extract text from prescription images)               │
        │                                                           │
        │  • Groq API (Llama 3.3 70B)                              │
        │    (Parse prescription text → JSON medications)          │
        │                                                           │
        │  • Telegram Bot API                                      │
        │    (Send reminder messages)                              │
        │                                                           │
        └───────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

### **1. Telegram Bot (`bot/`)**

**Purpose:** Interactive user interface for medication management

**Responsibilities:**
- Handle `/start` command and show main menu
- Accept prescription image uploads
- Manage interactive FSM-driven workflows (add, edit, confirm medications)
- Display user's active medications and schedules
- Send daily reminder notifications

**Key Components:**
- `bot/handlers/` — Message and callback handlers for each state
- `bot/states.py` — Finite State Machine state definitions (8 states)
- `bot/keyboards.py` — Inline buttons and reply keyboards
- Uses `APScheduler` to send scheduled reminders

**Dependencies:**
- Aiogram 3.x (Telegram framework)
- FastAPI backend (via httpx for REST calls)
- APScheduler (for scheduled reminders)

---

### **2. FastAPI Backend (`app/`)**

**Purpose:** Business logic, API endpoints, and orchestration of external services

**Responsibilities:**
- Accept prescription image files and call OCR service
- Accept prescription text and call LLM parsing service
- Persist medications and schedules to database
- Retrieve user medications for the bot
- Health checks and service monitoring

**Key Components:**

**Routers** (`app/routers/`):
- `ocr.py` — POST `/ocr` — Image upload & OCR
- `parse.py` — POST `/parse` — Text parsing with LLM
- `medications.py` — POST `/medications` & GET `/medications/{user_id}` — Medication CRUD

**Services** (`app/services/`):
- `ocr_service.py` — Call Gemini Vision API, clean text
- `llm_service.py` — Call Groq LLM, validate JSON response
- `medication_service.py` — Orchestrate persistence and scheduling
- `scheduler_service.py` — Create/manage APScheduler jobs

**Repositories** (`app/repositories/`):
- `user_repo.py` — User CRUD operations
- `medication_repo.py` — Medication CRUD operations
- `schedule_repo.py` — Schedule CRUD operations

**Models** (`app/models/`):
- `user.py` — User SQLAlchemy model
- `medication.py` — Medication SQLAlchemy model
- `schedule.py` — Schedule SQLAlchemy model

**Schemas** (`app/schemas/`):
- `medication.py` — Pydantic request/response schemas
- `schedule.py` — Schedule response schemas

---

### **3. MySQL Database**

**Purpose:** Persistent storage of user, medication, and schedule data

**Data Model:**

```
User (users table)
├── id (PK)
├── telegram_id (unique index) — Telegram user identifier
└── medications (relationship)
    ├── Medication (medications table)
    │   ├── id (PK)
    │   ├── user_id (FK) — Foreign key to users
    │   ├── name — Medication name
    │   ├── dosage_per_day — Number of doses (1-4)
    │   ├── notes — Instructions (e.g., "after meal")
    │   └── schedules (relationship)
    │       └── Schedule (schedules table)
    │           ├── id (PK)
    │           ├── medication_id (FK) — Foreign key to medications
    │           ├── time — HH:MM format (e.g., "08:00")
    │           ├── reminder_offset_minutes — Early reminder (default 5)
    │           └── duration_in_days — How long to remind (default 7)
```

**Cascade Rules:**
- Delete user → All their medications deleted
- Delete medication → All its schedules deleted

---

### **4. External Services**

#### **Google Gemini Vision API**
- **Function:** Extract text from prescription images (OCR)
- **Called by:** `app/services/ocr_service.py`
- **Returns:** Raw prescription text (may contain OCR errors)
- **Handles:** Multilingual prescriptions (Uzbek, Russian, English)

#### **Groq API (Llama 3.3 70B)**
- **Function:** Parse prescription text into structured medications
- **Called by:** `app/services/llm_service.py`
- **Input:** Raw OCR text
- **Returns:** JSON array of medications with:
  - `name` — Drug name
  - `dosage_per_day` — Doses per day (1-4)
  - `timing` — Timing hint (morning/afternoon/evening/custom)
  - `duration_in_days` — How long to take (optional)
  - `notes` — Instructions (optional)
- **Validation:** JSON mode enforces schema compliance

#### **APScheduler**
- **Function:** Schedule reminder jobs for specific times each day
- **When:** When user confirms medication with schedules
- **Jobs:** Two per time slot (reminder offset + exact time)
- **Cleanup:** Jobs auto-expire when `duration_in_days` passes
- **Delivery:** Fire-and-forget Telegram API messages

---

## Data Flow

### **Flow 1: Prescription Scanning → Reminder Setup**

```
1. User sends prescription image to Telegram bot
   ↓
2. Bot handler receives photo (handlers/image.py)
   ↓
3. Bot sends POST request to /ocr endpoint
   ├─ Includes: image bytes, filename
   ├─ Called by: app/routers/ocr.py
   └─ Handled by: app/services/ocr_service.py
   ↓
4. ocr_service.extract_text()
   ├─ Call Google Gemini Vision API with image
   ├─ Apply multilingual post-processing
   └─ Return cleaned text
   ↓
5. Bot receives OCR text
   ├─ Displays raw text to user
   └─ Stores in FSM state: data["ocr_text"]
   ↓
6. User requests parsing (clicks "Parse with AI")
   ↓
7. Bot sends POST request to /parse endpoint
   ├─ Includes: OCR text
   ├─ Called by: app/routers/parse.py
   └─ Handled by: app/services/llm_service.py
   ↓
8. llm_service.parse_prescription()
   ├─ Call Groq API with text + JSON schema prompt
   ├─ Validate response schema
   └─ Return list of MedicationLLM objects
   ↓
9. Bot receives structured medications
   ├─ Display first medication for confirmation
   └─ User can edit or confirm
   ↓
10. User confirms all medications (after edits)
    ↓
11. Bot sends POST request to /medications endpoint
    ├─ Includes: telegram_id, medication, times, offset, duration
    ├─ Called by: app/routers/medications.py
    └─ Handled by: app/services/medication_service.py
    ↓
12. medication_service.save_medication_with_schedules()
    ├─ Create/get User by telegram_id
    ├─ Create Medication record
    ├─ Create Schedule records (one per time)
    ├─ Call scheduler_service to create APScheduler jobs
    └─ Return saved objects
    ↓
13. Bot receives confirmation
    ├─ Display success message
    └─ Return to main menu
    ↓
14. APScheduler jobs fire at scheduled times
    ├─ First reminder (e.g., "Take in 5 mins")
    ├─ Exact time reminder ("Time to take your medicine")
    └─ Messages sent via Telegram Bot API

End: User receives daily reminders at specified times until duration expires
```

### **Flow 2: Manual Medication Entry**

```
1. User clicks "⌨️ Add Manually" in bot
   ↓
2. Bot enters FSM state: confirming_medication
   ├─ Initialize empty medication
   └─ Display template
   ↓
3. User clicks "Edit" to modify fields
   ↓
4. Bot collects edits through interactive states
   ├─ editing_field_choice — Select which field
   ├─ editing_field_value — Provide new value
   ├─ selecting_times — Choose HH:MM times
   ├─ selecting_reminder_offset — Choose early reminder
   ├─ selecting_duration — Choose how many days
   └─ Return to confirming_medication
   ↓
5. User clicks "✅ Confirm"
   ↓
6. Same as Flow 1, Step 11+
   (Bot calls /medications endpoint with user-entered data)

End: Medication saved and reminders scheduled
```

### **Flow 3: View Schedules**

```
1. User clicks "📋 View My Schedules" in bot
   ↓
2. Bot sends GET request to /medications/{telegram_id}/active
   ├─ Called by: app/routers/medications.py
   └─ Handled by: app/services/medication_service.py
   ↓
3. Service queries medications with active schedules
   ├─ Filter: Only medications with >= 1 schedule
   ├─ Group: schedule times by medication
   └─ Return ActiveMedication objects
   ↓
4. Bot receives medications list
   ├─ Format prettily with times, offsets, duration
   ├─ Display as message to user
   └─ Offer edit/delete options (future)

End: User sees all active medications with their daily schedules
```

---

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Language** | Python | 3.10+ | Runtime |
| **Bot** | Aiogram | 3.6.0 | Telegram bot framework |
| **Backend** | FastAPI | 0.111.0 | REST API framework |
| **Server** | Uvicorn | 0.29.0 | ASGI server |
| **Database ORM** | SQLAlchemy | 2.0.30 | Async ORM |
| **DB Driver** | aiomysql | 0.2.0 | Async MySQL driver |
| **Database** | MySQL | 8.0 | Relational database |
| **Task Scheduler** | APScheduler | 3.10.4 | Job scheduling |
| **HTTP Client** | httpx | 0.27.0 | Async HTTP requests |
| **Config** | pydantic-settings | 2.2.1 | Env var management |
| **LLM API** | Groq | 0.18.0+ | LLM inference |
| **Containerization** | Docker | Latest | Container runtime |
| **Orchestration** | Docker Compose | Latest | Multi-container setup |

---

## Design Decisions

### **1. Async/Await Throughout**

**Decision:** Use async Python (asyncio, async SQLAlchemy, async httpx) everywhere.

**Rationale:**
- Bot polling is naturally asynchronous (many concurrent users)
- Database queries don't block bot operations
- Multiple concurrent API requests to Gemini/Groq
- APScheduler runs concurrent reminder jobs

**Impact:**
- Higher throughput, lower resource usage
- Requires async-compatible libraries (aiomysql, aiogram, httpx)
- Eliminates thread management complexity

---

### **2. Separated Services (Bot ≠ API)**

**Decision:** Run bot and API as separate containers/processes.

**Rationale:**
- **Scalability:** Can run multiple bot instances or multiple API instances independently
- **Resilience:** If API crashes, bot can still send cached reminders
- **Deployment:** Bot and API on different release schedules
- **Debugging:** Easier to trace issues in isolated components

**Impact:**
- Bot calls API via HTTP (httpx)
- Requires Docker Compose for local dev/prod
- Bot uses in-memory FSM storage (MemoryStorage) — no persistence of state

---

### **3. FSM State Machine in Bot**

**Decision:** Use Aiogram's Finite State Machine to guide users through workflows.

**Rationale:**
- Clear user experience: each step is explicit
- Prevents invalid operations (e.g., can't confirm before defining times)
- Easy to debug user workflows

**Impact:**
- 8 states for prescription flow (see [BOT_COMMANDS.md](BOT_COMMANDS.md#fsm-state-machine))
- State stored in-memory (lost on bot restart) — acceptable for temporary UI state
- Allows users to cancel at any step via /start or timeout

---

### **4. APScheduler for Reminders**

**Decision:** Use APScheduler for job scheduling instead of cron or external scheduler.

**Rationale:**
- In-process scheduling — no external service needed
- Flexible: can dynamically create/delete jobs
- Per-schedule offset reminders (flexible reminder timing)
- Easy job cleanup when medication expires

**Limitations:**
- Jobs stored in-memory; lost on bot restart
- Not suitable for massive scale (thousands of concurrent jobs)
- Better for small-to-medium deployments

**Future Alternative:** External job queue (Celery + Redis) for large scale.

---

### **5. Repository Pattern**

**Decision:** Data access via repositories, not direct model usage.

**Rationale:**
- Single source of truth for data operations
- Easy to swap implementations (e.g., PostgreSQL instead of MySQL)
- Simpler testing (can mock repositories)
- Encapsulates query logic

**Impact:**
- `UserRepository`, `MedicationRepository`, `ScheduleRepository` in `app/repositories/`
- Services use repositories, not direct SQLAlchemy queries
- Eliminates tight coupling to database layer

---

### **6. Pydantic Schemas for Validation**

**Decision:** Use Pydantic for request/response validation, not Marshmallow.

**Rationale:**
- Single tool for both validation and serialization
- Built into FastAPI (auto-generated OpenAPI docs)
- Strong type hints integration
- Field validators for business logic (e.g., dosage 1-4)

**Impact:**
- `MedicationCreate`, `MedicationRead`, `MedicationLLM` in `app/schemas/medication.py`
- FastAPI auto-validates incoming requests
- Type hints improve IDE autocomplete

---

### **7. Cascade Deletes**

**Decision:** Delete user → deletes all medications → deletes all schedules.

**Rationale:**
- No orphaned data in database
- Simplifies cleanup logic
- Aligns with domain: a user's medications have no meaning without the user

**Syntax:** SQLAlchemy `cascade="all, delete-orphan"`

**Impact:**
- Deleted user = fully cleaned up from database
- One DELETE query cascades through all relationships

---

## Async Architecture

All components use Python's `asyncio` for concurrent operations:

```
Bot Polling (async)
├─ Receive message #1 → handler(msg1)
├─ Receive message #2 → handler(msg2)  [concurrently]
├─ Each handler: await ocr_service.extract_text()
│  └─ Calls await gemini_api.process_image() [non-blocking]
├─ Each handler: await medication_repo.save()
│  └─ Calls await db_session.commit() [non-blocking]
└─ APScheduler jobs [async callbacks]
   ├─ Job A: send reminder at 08:00
   ├─ Job B: send reminder at 14:00 [concurrent]
   └─ Each job: await bot.send_message() [fire-and-forget]
```

**Key Benefits:**
- Single-threaded but highly concurrent
- No lock contention
- Lower memory per concurrent operation
- Scales to thousands of concurrent users

**Key Requirement:**
- All database queries, API calls, and bot operations must use `await`
- Blocking calls (e.g., `requests.get()`) will freeze the entire bot

---

## See Also

- [DATABASE.md](DATABASE.md) — Detailed schema and model relationships
- [API_REFERENCE.md](API_REFERENCE.md) — Endpoint specifications
- [BOT_COMMANDS.md](BOT_COMMANDS.md) — Bot workflows and FSM states
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — Extending the system
- [DEPLOYMENT.md](DEPLOYMENT.md) — Running in production

---

**Last Updated:** April 2026  
**Status:** Complete
