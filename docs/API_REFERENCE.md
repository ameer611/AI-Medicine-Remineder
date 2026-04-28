# API Reference

Complete reference for all FastAPI endpoints, request/response schemas, error codes, and examples.

**Table of Contents**
- [Base URL](#base-url)
- [Authentication](#authentication)
- [OCR Endpoint](#ocr-endpoint)
- [Parse Endpoint](#parse-endpoint)
- [Medications Endpoints](#medications-endpoints)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Rate Limiting](#rate-limiting)

---

## Base URL

```
Development:  http://localhost:8000
Docker:       http://api:8000
Production:   https://api.dori-scheduler.example.com (if deployed)
```

---

## Authentication

**Current Status:** No authentication required.

All endpoints are public. For production deployment, consider:
- API key authentication per Telegram bot
- JWT tokens for endpoint authorization
- Rate limiting per IP/bot

---

## OCR Endpoint

Extract text from a prescription image using Google Gemini Vision API.

### **POST /ocr**

**Purpose:** Upload an image of a prescription and extract readable text via OCR.

**Request**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File (multipart) | Yes | Image file (PNG, JPG, JPEG, etc.) |

**Content-Type:** `multipart/form-data`

**Response (200 OK)**

```json
{
  "text": "Aspirin 500mg: take one tablet twice daily after meals.\nVitamin D: take one capsule daily with breakfast.\nPrescribed: Dr. Smith, 2024-04-15"
}
```

**Response Schema:**

```python
{
  "text": str  # Extracted prescription text (may contain OCR errors)
}
```

### **Error Responses**

| Status | Response | Reason |
|--------|----------|--------|
| 400 | `{"detail": "File must be an image"}` | Content-Type is not image/* |
| 400 | `{"detail": "Empty file"}` | File uploaded is 0 bytes |
| 422 | `{"detail": "OCR service failed: API error"}` | Gemini Vision API error or timeout |
| 500 | `{"detail": "Internal server error"}` | Unexpected error on server |

### **cURL Example**

```bash
curl -X POST http://localhost:8000/ocr \
  -F "file=@prescription.jpg"

# Response:
# {
#   "text": "Aspirin 500mg twice daily..."
# }
```

### **Python Example**

```python
import httpx

async def extract_prescription_text(image_path: str) -> str:
    async with httpx.AsyncClient() as client:
        with open(image_path, "rb") as f:
            response = await client.post(
                "http://localhost:8000/ocr",
                files={"file": f}
            )
        response.raise_for_status()
        return response.json()["text"]

# Usage
text = await extract_prescription_text("prescription.jpg")
print(text)
```

---

## Parse Endpoint

Parse prescription text and extract structured medication information using Groq LLM.

### **POST /parse**

**Purpose:** Send raw prescription text and receive structured medications with dosage, timing, and duration.

**Request**

```json
{
  "text": "Aspirin 500mg: take one tablet twice daily after meals for 7 days.\nVitamin D: take one capsule daily for 30 days."
}
```

**Request Schema:**

```python
class ParseRequest(BaseModel):
    text: str  # Non-empty prescription text
```

**Content-Type:** `application/json`

**Response (200 OK)**

```json
{
  "medications": [
    {
      "name": "Aspirin 500mg",
      "dosage_per_day": 2,
      "timing": "custom",
      "duration_in_days": 7,
      "notes": "after meals"
    },
    {
      "name": "Vitamin D",
      "dosage_per_day": 1,
      "timing": "morning",
      "duration_in_days": 30,
      "notes": null
    }
  ]
}
```

**Response Schema:**

```python
class MedicationLLM(BaseModel):
    name: str  # Medication name
    dosage_per_day: int  # 1-4 doses per day (clamped by LLM)
    timing: Literal["morning", "afternoon", "evening", "custom"]
    duration_in_days: int | None  # How many days to take (nullable)
    notes: str | None  # Instructions (e.g., "after meal")

class ParseResponse(BaseModel):
    medications: list[MedicationLLM]
```

### **Error Responses**

| Status | Response | Reason |
|--------|----------|--------|
| 400 | `{"detail": "text must not be empty"}` | Text field is empty or only whitespace |
| 422 | `{"detail": "Validation error"}` | Invalid JSON or missing required fields |
| 502 | `{"detail": "LLM service failed: API error"}` | Groq API error, timeout, or rate limit |
| 500 | `{"detail": "Internal server error"}` | Unexpected error on server |

### **cURL Example**

```bash
curl -X POST http://localhost:8000/parse \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Aspirin 500mg twice daily after meals for 7 days"
  }'

# Response:
# {
#   "medications": [
#     {
#       "name": "Aspirin 500mg",
#       "dosage_per_day": 2,
#       "timing": "custom",
#       "duration_in_days": 7,
#       "notes": "after meals"
#     }
#   ]
# }
```

### **Python Example**

```python
import httpx

async def parse_prescription(text: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/parse",
            json={"text": text}
        )
    response.raise_for_status()
    return response.json()["medications"]

# Usage
medications = await parse_prescription("Aspirin twice daily for 7 days")
for med in medications:
    print(f"{med['name']}: {med['dosage_per_day']}x per day")
```

---

## Medications Endpoints

Save and retrieve medications with their daily schedules.

### **POST /medications**

**Purpose:** Save a medication with its daily schedule times and create APScheduler reminder jobs.

**Request**

```json
{
  "telegram_id": 123456789,
  "medication": {
    "name": "Aspirin 500mg",
    "dosage_per_day": 2,
    "timing": "custom",
    "notes": "after meals"
  },
  "times": ["08:00", "20:00"],
  "reminder_offset_minutes": 5,
  "duration_in_days": 7
}
```

**Request Schema:**

```python
class MedicationCreate(BaseModel):
    name: str  # 1-255 chars
    dosage_per_day: int  # 1-4
    timing: Literal["morning", "afternoon", "evening", "custom"]
    notes: str | None

class SaveMedicationRequest(BaseModel):
    telegram_id: int  # Telegram user ID
    medication: MedicationCreate
    times: list[str]  # HH:MM format, must match dosage_per_day count
    reminder_offset_minutes: int
    duration_in_days: int
```

**Content-Type:** `application/json`

**Response (200 OK)**

```json
{
  "medication": {
    "id": 42,
    "user_id": 1,
    "name": "Aspirin 500mg",
    "dosage_per_day": 2,
    "timing": "custom",
    "notes": "after meals"
  },
  "schedules": [
    {
      "id": 101,
      "time": "08:00",
      "reminder_offset_minutes": 5,
      "duration_in_days": 7
    },
    {
      "id": 102,
      "time": "20:00",
      "reminder_offset_minutes": 5,
      "duration_in_days": 7
    }
  ]
}
```

**Response Schema:**

```python
class SaveMedicationResponse(BaseModel):
    medication: MedicationRead
    schedules: list[ScheduleRead]
```

### **Error Responses**

| Status | Response | Reason |
|--------|----------|--------|
| 400 | `{"detail": "At least one time is required"}` | times array is empty |
| 400 | `{"detail": "Expected N time(s), got M"}` | Length mismatch: times count ≠ dosage_per_day |
| 400 | `{"detail": "Duplicate times are not allowed"}` | Same time appears multiple times |
| 404 | `{"detail": "User not found"}` | Telegram user doesn't exist (creation happens in later logic) |
| 500 | `{"detail": "Database error"}` | Failed to save to database |

### **cURL Example**

```bash
curl -X POST http://localhost:8000/medications \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": 123456789,
    "medication": {
      "name": "Aspirin 500mg",
      "dosage_per_day": 2,
      "timing": "custom",
      "notes": "after meals"
    },
    "times": ["08:00", "20:00"],
    "reminder_offset_minutes": 5,
    "duration_in_days": 7
  }'
```

### **Python Example**

```python
import httpx

async def save_medication(
    telegram_id: int,
    name: str,
    dosage_per_day: int,
    times: list[str],
    notes: str | None = None
) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/medications",
            json={
                "telegram_id": telegram_id,
                "medication": {
                    "name": name,
                    "dosage_per_day": dosage_per_day,
                    "timing": "custom",
                    "notes": notes
                },
                "times": times,
                "reminder_offset_minutes": 5,
                "duration_in_days": 7
            }
        )
    response.raise_for_status()
    return response.json()

# Usage
result = await save_medication(
    telegram_id=123456789,
    name="Aspirin 500mg",
    dosage_per_day=2,
    times=["08:00", "20:00"],
    notes="after meals"
)
print(f"Saved medication: {result['medication']['name']}")
```

---

### **GET /medications/{user_id}**

**Purpose:** Retrieve all medications (with schedules) for a given internal user ID.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | int | Internal user ID (NOT telegram_id) |

**Query Parameters**

None

**Response (200 OK)**

```json
[
  {
    "id": 42,
    "user_id": 1,
    "name": "Aspirin 500mg",
    "dosage_per_day": 2,
    "timing": "custom",
    "notes": "after meals"
  },
  {
    "id": 43,
    "user_id": 1,
    "name": "Vitamin D",
    "dosage_per_day": 1,
    "timing": "morning",
    "notes": null
  }
]
```

**Response Schema:** `list[MedicationRead]`

### **Error Responses**

| Status | Response | Reason |
|--------|----------|--------|
| 404 | `{"detail": "User not found"}` | user_id doesn't exist |

### **cURL Example**

```bash
curl http://localhost:8000/medications/1
```

### **Python Example**

```python
import httpx

async def get_user_medications(user_id: int) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:8000/medications/{user_id}")
    response.raise_for_status()
    return response.json()

# Usage
medications = await get_user_medications(1)
for med in medications:
    print(f"{med['name']}: {med['dosage_per_day']}x daily")
```

---

### **GET /medications/{user_id}/active**

**Purpose:** Retrieve medications with at least one active schedule for a given Telegram user.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | int | Telegram user ID |

**Note:** This uses the external `user_id` parameter but internally treats it as `telegram_id` for lookup.

**Response (200 OK)**

```json
{
  "medications": [
    {
      "name": "Aspirin 500mg",
      "dosage_per_day": 2,
      "times": ["08:00", "20:00"],
      "reminder_offset_minutes": 5
    },
    {
      "name": "Vitamin D",
      "dosage_per_day": 1,
      "times": ["09:00"],
      "reminder_offset_minutes": 15
    }
  ]
}
```

**Response Schema:**

```python
class ActiveMedication(BaseModel):
    name: str
    dosage_per_day: int
    times: list[str]
    reminder_offset_minutes: int

class ActiveMedicationsResponse(BaseModel):
    medications: list[ActiveMedication]
```

### **Error Responses**

| Status | Response | Reason |
|--------|----------|--------|
| 404 | `{"detail": "User not found"}` | Telegram user doesn't exist |

### **cURL Example**

```bash
curl "http://localhost:8000/medications/123456789/active"
```

---

## Error Handling

### **HTTP Status Codes**

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid input (empty text, empty file, etc.) |
| 404 | Not Found | User or medication doesn't exist |
| 422 | Unprocessable Entity | Schema validation failure |
| 502 | Bad Gateway | External API error (Gemini, Groq) |
| 500 | Internal Server Error | Unexpected server error |

### **Error Response Format**

All errors return JSON with standard format:

```json
{
  "detail": "Description of what went wrong"
}
```

### **Handling Errors in Code**

```python
import httpx

try:
    response = await client.post("http://localhost:8000/parse", json={"text": ""})
    response.raise_for_status()
    data = response.json()
except httpx.HTTPStatusError as e:
    print(f"Error {e.response.status_code}: {e.response.json()['detail']}")
except httpx.RequestError as e:
    print(f"Connection error: {e}")
```

---

## Examples

### **Complete Workflow: Scan → Parse → Save**

```python
import httpx

async def complete_prescription_flow(
    image_path: str,
    telegram_id: int,
    reminder_offset: int = 5,
    duration_days: int = 7
):
    """Full workflow from image to scheduled reminders."""
    
    async with httpx.AsyncClient() as client:
        # Step 1: OCR the image
        print("1. Scanning prescription...")
        with open(image_path, "rb") as f:
            ocr_response = await client.post(
                "http://localhost:8000/ocr",
                files={"file": f}
            )
        ocr_response.raise_for_status()
        ocr_text = ocr_response.json()["text"]
        print(f"   Extracted: {ocr_text[:100]}...")
        
        # Step 2: Parse with LLM
        print("2. Parsing with AI...")
        parse_response = await client.post(
            "http://localhost:8000/parse",
            json={"text": ocr_text}
        )
        parse_response.raise_for_status()
        medications = parse_response.json()["medications"]
        print(f"   Found {len(medications)} medications")
        
        # Step 3: Save each medication
        print("3. Saving medications...")
        for med in medications:
            # Generate times based on dosage
            times = []
            if med["dosage_per_day"] == 1:
                times = ["09:00"]
            elif med["dosage_per_day"] == 2:
                times = ["08:00", "20:00"]
            elif med["dosage_per_day"] == 3:
                times = ["08:00", "14:00", "20:00"]
            elif med["dosage_per_day"] == 4:
                times = ["07:00", "11:00", "15:00", "19:00"]
            
            save_response = await client.post(
                "http://localhost:8000/medications",
                json={
                    "telegram_id": telegram_id,
                    "medication": {
                        "name": med["name"],
                        "dosage_per_day": med["dosage_per_day"],
                        "timing": med.get("timing", "custom"),
                        "notes": med.get("notes")
                    },
                    "times": times,
                    "reminder_offset_minutes": reminder_offset,
                    "duration_in_days": duration_days
                }
            )
            save_response.raise_for_status()
            print(f"   ✓ {med['name']}")
        
        print("Done! Reminders scheduled.")

# Usage
import asyncio
asyncio.run(complete_prescription_flow(
    "prescription.jpg",
    telegram_id=123456789
))
```

---

## Rate Limiting

**Current Status:** No rate limiting implemented.

**Recommendations for Production:**
- Gemini Vision API: 60 requests/minute per project
- Groq API: 30 requests/minute (free tier)
- Telegram Bot API: 30 messages/second per chat

Implement rate limiting per endpoint/client:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/parse")
@limiter.limit("30/minute")
async def parse_endpoint(...):
    ...
```

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) — How these endpoints fit in the system
- [BOT_COMMANDS.md](BOT_COMMANDS.md) — How the bot calls these endpoints
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#adding-a-new-endpoint) — Adding new endpoints

---

**Last Updated:** April 2026  
**Status:** Complete
