# Database Schema & Design

This document provides complete documentation of the database schema, models, relationships, and repository layer.

**Table of Contents**
- [ER Diagram](#er-diagram)
- [Data Models](#data-models)
- [Relationships](#relationships)
- [Indexes & Constraints](#indexes--constraints)
- [Repository Layer](#repository-layer)
- [Database Operations](#database-operations)

---

## ER Diagram

### Visual Representation

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATABASE SCHEMA                          │
└─────────────────────────────────────────────────────────────────┘

        ┌──────────────────────┐
        │      USERS           │
        ├──────────────────────┤
        │ id (PK)              │◄──────────┐
        │ telegram_id (UQ)     │           │
        │ [timestamps]         │           │
        └──────────────────────┘           │
                   │                       │
                   │ 1:N                   │
                   │ (One user has many   │
                   │  medications)        │
                   │                       │
                   ▼                       │
        ┌──────────────────────┐           │
        │   MEDICATIONS        │           │
        ├──────────────────────┤           │
        │ id (PK)              │───────────┤
        │ user_id (FK) ────────┼───────────┘
        │ name                 │
        │ dosage_per_day (1-4) │
        │ notes (nullable)     │
        │ [timestamps]         │
        └──────────────────────┘
                   │
                   │ 1:N
                   │ (One medication has
                   │  many schedules)
                   │
                   ▼
        ┌──────────────────────┐
        │   SCHEDULES          │
        ├──────────────────────┤
        │ id (PK)              │
        │ medication_id (FK)   │
        │ time (HH:MM)         │
        │ reminder_offset_min  │
        │ duration_in_days     │
        │ [timestamps]         │
        └──────────────────────┘

Cascade Rules:
  • Delete User → Delete all Medications → Delete all Schedules
  • Delete Medication → Delete all Schedules
  • Delete Schedule → (orphaned; cleaned by cascade)
```

---

## Data Models

### **1. User Model**

**File:** [app/models/user.py](../app/models/user.py)

**Table:** `users`

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | Internal user ID |
| `telegram_id` | BIGINT | UNIQUE, NOT NULL, INDEX | Telegram user ID (unique per bot) |

**Relationships:**
- **One-to-Many with Medications:** One user can have multiple medications
  - Cascade delete: Deleting a user deletes all their medications

**Example Record:**
```python
User(id=1, telegram_id=123456789)
```

**SQLAlchemy Code:**
```python
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    
    medications: Mapped[list["Medication"]] = relationship(
        "Medication", back_populates="user", cascade="all, delete-orphan"
    )
```

---

### **2. Medication Model**

**File:** [app/models/medication.py](../app/models/medication.py)

**Table:** `medications`

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | Internal medication ID |
| `user_id` | INT | FOREIGN KEY (users.id), NOT NULL | Reference to user (cascade delete) |
| `name` | VARCHAR(255) | NOT NULL | Medication name (e.g., "Aspirin 500mg") |
| `dosage_per_day` | INT | NOT NULL | Number of doses per day (1, 2, 3, or 4) |
| `notes` | TEXT | NULL | Instructions (e.g., "take after meal", "with water") |

**Relationships:**
- **Many-to-One with User:** Each medication belongs to exactly one user
- **One-to-Many with Schedules:** One medication can have multiple time slots per day
  - Cascade delete: Deleting a medication deletes all its schedules

**Constraints:**
- `dosage_per_day` validated by LLM parser (1-4 only)
- `name` cannot be empty (min_length=1)

**Example Records:**
```python
Medication(id=1, user_id=1, name="Aspirin 500mg", dosage_per_day=2, notes="after meal")
Medication(id=2, user_id=1, name="Vitamin D", dosage_per_day=1, notes=None)
```

**SQLAlchemy Code:**
```python
class Medication(Base):
    __tablename__ = "medications"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage_per_day: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    user: Mapped["User"] = relationship("User", back_populates="medications")
    schedules: Mapped[list["Schedule"]] = relationship(
        "Schedule", back_populates="medication", cascade="all, delete-orphan"
    )
```

---

### **3. Schedule Model**

**File:** [app/models/schedule.py](../app/models/schedule.py)

**Table:** `schedules`

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | Internal schedule ID |
| `medication_id` | INT | FOREIGN KEY (medications.id), NOT NULL | Reference to medication (cascade delete) |
| `time` | VARCHAR(5) | NOT NULL | Time in HH:MM format (e.g., "08:00", "14:30") |
| `reminder_offset_minutes` | INT | NOT NULL, DEFAULT 5 | Minutes before time to send reminder (e.g., 5, 15, 30) |
| `duration_in_days` | INT | NOT NULL, DEFAULT 7 | How many days to send reminders (e.g., 7, 14, 30) |

**Relationships:**
- **Many-to-One with Medication:** Each schedule belongs to exactly one medication

**Constraints:**
- `time` format: Must be valid HH:MM (enforced by bot UI)
- `reminder_offset_minutes` > 0
- `duration_in_days` > 0
- Unique constraint: (medication_id, time) — No duplicate times for same medication

**Example Records:**
```python
# Aspirin twice daily with reminders
Schedule(id=1, medication_id=1, time="08:00", reminder_offset_minutes=5, duration_in_days=7)
Schedule(id=2, medication_id=1, time="20:00", reminder_offset_minutes=5, duration_in_days=7)

# Vitamin D once daily
Schedule(id=3, medication_id=2, time="09:00", reminder_offset_minutes=15, duration_in_days=30)
```

**SQLAlchemy Code:**
```python
class Schedule(Base):
    __tablename__ = "schedules"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    medication_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("medications.id", ondelete="CASCADE"), nullable=False
    )
    time: Mapped[str] = mapped_column(String(5), nullable=False)
    reminder_offset_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    duration_in_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    
    medication: Mapped["Medication"] = relationship("Medication", back_populates="schedules")
```

---

## Relationships

### **Data Hierarchy**

```
User (1)
  ├── Medication (N)
  │     ├── Schedule (N)
  │     └── Schedule (N)
  └── Medication (N)
        ├── Schedule (N)
        └── Schedule (N)
```

**Example:**
```
User: telegram_id=123456789
  ├── Medication: Aspirin 500mg, 2x daily
  │     ├── Schedule: 08:00 (5 min offset, 7 days)
  │     └── Schedule: 20:00 (5 min offset, 7 days)
  └── Medication: Vitamin D, 1x daily
        └── Schedule: 09:00 (15 min offset, 30 days)
```

### **Cascade Delete Behavior**

**Scenario 1: Delete a User**
```
DELETE FROM users WHERE id = 1
  → Cascades to all medications for user 1
    → DELETE FROM medications WHERE user_id = 1
      → Cascades to all schedules for those medications
        → DELETE FROM schedules WHERE medication_id IN (...)
```

**Scenario 2: Delete a Medication**
```
DELETE FROM medications WHERE id = 5
  → Cascades to all schedules for medication 5
    → DELETE FROM schedules WHERE medication_id = 5
```

**Scenario 3: Delete a Schedule**
```
DELETE FROM schedules WHERE id = 10
  → No cascade (schedules are leaf nodes)
  → Medication and User remain
```

---

## Indexes & Constraints

### **Indexes**

| Table | Column(s) | Type | Purpose |
|-------|-----------|------|---------|
| `users` | `telegram_id` | UNIQUE INDEX | Fast lookup by Telegram ID |
| `medications` | `user_id` | (auto FK index) | Fast lookup by user |
| `schedules` | `medication_id` | (auto FK index) | Fast lookup by medication |

### **Constraints**

| Table | Constraint | Type | Reason |
|-------|-----------|------|--------|
| `users` | `telegram_id` UNIQUE | Business logic | Each Telegram user is unique |
| `medications` | `user_id` FK ON CASCADE DELETE | Referential integrity | Maintain consistency |
| `schedules` | `medication_id` FK ON CASCADE DELETE | Referential integrity | Maintain consistency |
| `medications` | `dosage_per_day` ∈ [1,4] | Validation (Pydantic) | App enforces via schema |
| `schedules` | `time` format HH:MM | Validation (UI) | Bot restricts choices |

---

## Repository Layer

The repository pattern abstracts database operations. Each repository implements CRUD operations for one model.

### **UserRepository**

**Location:** [app/repositories/user_repo.py](../app/repositories/user_repo.py)

**Methods:**

```python
class UserRepository:
    async def get_by_id(self, user_id: int) -> User | None:
        """Fetch user by internal ID."""
        
    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Fetch user by Telegram ID (most common operation)."""
        
    async def get_or_create_by_telegram_id(self, telegram_id: int) -> User:
        """Get existing user or create new one."""
        
    async def create(self, telegram_id: int) -> User:
        """Create new user."""
        
    async def delete(self, user_id: int) -> None:
        """Delete user (cascades to medications and schedules)."""
```

**Example Usage:**
```python
repo = UserRepository(session)

# Get existing user
user = await repo.get_by_telegram_id(123456789)

# Create if not exists
user = await repo.get_or_create_by_telegram_id(123456789)
```

---

### **MedicationRepository**

**Location:** [app/repositories/medication_repo.py](../app/repositories/medication_repo.py)

**Methods:**

```python
class MedicationRepository:
    async def create(self, medication_data: MedicationCreate) -> Medication:
        """Create new medication for a user."""
        
    async def get_by_id(self, medication_id: int) -> Medication | None:
        """Fetch medication by ID."""
        
    async def get_by_user_id(self, user_id: int) -> list[Medication]:
        """Fetch all medications for a user."""
        
    async def update(self, medication_id: int, update_data: dict) -> Medication:
        """Update medication fields."""
        
    async def delete(self, medication_id: int) -> None:
        """Delete medication (cascades to schedules)."""
```

**Example Usage:**
```python
repo = MedicationRepository(session)

# Create medication
med = await repo.create(MedicationCreate(
    user_id=1,
    name="Aspirin 500mg",
    dosage_per_day=2,
    notes="after meal"
))

# Get all for user
medications = await repo.get_by_user_id(1)
```

---

### **ScheduleRepository**

**Location:** [app/repositories/schedule_repo.py](../app/repositories/schedule_repo.py)

**Methods:**

```python
class ScheduleRepository:
    async def create(self, schedule_data: ScheduleCreate) -> Schedule:
        """Create new schedule for a medication."""
        
    async def get_by_id(self, schedule_id: int) -> Schedule | None:
        """Fetch schedule by ID."""
        
    async def get_by_medication_id(self, medication_id: int) -> list[Schedule]:
        """Fetch all schedules for a medication."""
        
    async def update(self, schedule_id: int, update_data: dict) -> Schedule:
        """Update schedule fields."""
        
    async def delete(self, schedule_id: int) -> None:
        """Delete schedule."""
```

**Example Usage:**
```python
repo = ScheduleRepository(session)

# Create schedule
schedule = await repo.create(ScheduleCreate(
    medication_id=1,
    time="08:00",
    reminder_offset_minutes=5,
    duration_in_days=7
))

# Get all for medication
schedules = await repo.get_by_medication_id(1)
```

---

## Database Operations

### **Connection Setup**

**File:** [app/database.py](../app/database.py)

```python
# Async engine initialization
engine = create_async_engine(
    settings.DATABASE_URL,  # e.g., mysql+aiomysql://user:pass@host:port/db
    echo=False,
    future=True
)

# Async session factory
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Base class for models
class Base(DeclarativeBase):
    pass

# Dependency injection for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

### **Creating Tables**

```python
# Initialize database (create all tables)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

### **Sample Queries**

#### **Get User with All Medications and Schedules**

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Efficient query with eager loading
stmt = select(User).where(User.telegram_id == 123456789).options(
    selectinload(User.medications).selectinload(Medication.schedules)
)
user = await session.execute(stmt)
```

#### **Get All Active Medications (with schedules)**

```python
stmt = select(Medication).where(
    Medication.user_id == user_id
).options(
    selectinload(Medication.schedules)
)
medications = await session.execute(stmt)
```

#### **Insert New Medication with Schedules**

```python
# Create medication
medication = Medication(
    user_id=user_id,
    name="Aspirin",
    dosage_per_day=2,
    notes="after meal"
)
session.add(medication)
await session.flush()  # Get medication.id

# Create schedules
for time_str in ["08:00", "20:00"]:
    schedule = Schedule(
        medication_id=medication.id,
        time=time_str,
        reminder_offset_minutes=5,
        duration_in_days=7
    )
    session.add(schedule)

await session.commit()
```

#### **Delete Medication (cascades to schedules)**

```python
medication = await session.get(Medication, medication_id)
await session.delete(medication)
await session.commit()
```

---

## Database Initialization

### **First-Time Setup**

```bash
# Docker (automatic)
docker-compose up -d --build

# Local development
export DATABASE_URL="mysql+aiomysql://user:pass@localhost:3306/dori_scheduler"
python -c "from app.database import init_db; asyncio.run(init_db())"
```

### **Connection String Format**

```
mysql+aiomysql://[user]:[password]@[host]:[port]/[database]

Examples:
- Docker: mysql+aiomysql://dori:secret@mysql:3306/dori_scheduler
- Local:  mysql+aiomysql://root:password@localhost:3306/dori_scheduler
```

---

## Performance Considerations

### **Current Bottlenecks**

1. **N+1 Query Problem**
   - Solution: Use `selectinload()` to eagerly load relationships
   - Example: See "Get User with All Medications" above

2. **In-Memory State (APScheduler)**
   - Issue: Jobs lost on bot restart
   - Solution: For production, use external job queue (Celery + Redis, or database-backed scheduler)

### **Optimization Tips**

1. **Index common queries:** Telegram ID lookup is already indexed ✅
2. **Batch operations:** Update multiple medications in one query
3. **Connection pooling:** SQLAlchemy handles this automatically (pool_pre_ping=True recommended)
4. **Query complexity:** For 1000+ medications, consider pagination

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) — System components and data flow
- [API_REFERENCE.md](API_REFERENCE.md) — API schemas (MedicationCreate, ScheduleRead, etc.)
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#adding-a-new-database-model) — Adding new models
- [DEPLOYMENT.md](DEPLOYMENT.md#database-initialization) — Production database setup

---

**Last Updated:** April 2026  
**Status:** Complete
