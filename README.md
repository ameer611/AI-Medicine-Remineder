# Dori Scheduler - Medication Reminder System

Dori Scheduler is a robust, containerized medication reminder system featuring a FastAPI backend and a Telegram bot interface. It is designed to help users manage their medication schedules effectively by providing interactive bot commands, OCR-based prescription scanning, and dynamic scheduling powered by Large Language Models.

## 📚 Documentation

**Complete documentation is available in the [`docs/`](./docs/) folder.**

Quick links:
- **[Architecture & Design](./docs/ARCHITECTURE.md)** — System overview, data flows, technology stack
- **[Database Schema](./docs/DATABASE.md)** — Complete ER diagram and model relationships
- **[API Reference](./docs/API_REFERENCE.md)** — All endpoints with examples
- **[Bot Commands](./docs/BOT_COMMANDS.md)** — FSM states, handlers, workflows
- **[User Guide](./docs/USER_GUIDE.md)** — How to use the Telegram bot
- **[Developer Guide](./docs/DEVELOPER_GUIDE.md)** — Local setup, extending the codebase
- **[Deployment & Operations](./docs/DEPLOYMENT.md)** — Production deployment, monitoring

Start with the [**Documentation Index**](./docs/README.md) for guided navigation by role.

---

## 🌟 Features

- **Telegram Bot Interface:** User-friendly bot built with Aiogram to add, manage, and view medications.
- **Smart Parsing with LLMs:** Automatically extracts schedules, dosages, and durations from natural language inputs using the Cerebras LLM API.
- **OCR Prescription Scanning:** Users can upload images of their prescriptions. The system parses them via Google Gemini or EasyOCR to automatically create medication reminders.
- **Automated Daily Reminders:** Integrated with APScheduler to send timely medication reminders based on complex daily schedules.
- **Interactive Management & FSM:** Uses Finite State Machines (FSM) to guide users through adding, editing, or deleting active medications interactively.
- **Microservices Architecture:** Fully containerized setup via `docker-compose` separating the Telegram bot, the backend API, and a MySQL database.

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Backend API:** FastAPI, Uvicorn
- **Telegram Bot:** Aiogram 3.x
- **Database:** MySQL 8.0, SQLAlchemy (Async ORM), aiomysql
- **Task Scheduling:** APScheduler
- **AI & OCR Integrations:** Cerebras API, Google Gemini API, ocr.space
- **Containerization:** Docker, Docker Compose

## 📂 Project Structure

```text
dori_scheduler/
├── app/                  # FastAPI Backend
│   ├── models/           # SQLAlchemy Database Models
│   ├── repositories/     # Database operation abstractions
│   ├── routers/          # FastAPI Endpoints
│   ├── schemas/          # Pydantic validation schemas
│   ├── services/         # Core business logic (OCR, LLM, Scheduling)
│   ├── config.py         # App Configuration
│   ├── database.py       # Database connection setup
│   └── main.py           # FastAPI entrypoint
├── bot/                  # Telegram Bot Interface
│   ├── handlers/         # Message, callback, and command handlers
│   ├── keyboards.py      # Inline and Reply keyboards definition
│   ├── states.py         # Aiogram FSM states
│   └── __init__.py
├── docker-compose.yml    # Docker services orchestrator
├── Dockerfile            # Container build instructions
├── .env.example          # Template for required environment variables
├── requirements.txt      # Python dependencies
├── run_api.py            # API startup script
└── run_bot.py            # Bot startup script
```

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose installed on your machine.
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather).
- API keys for Cerebras and/or Google Gemini (for advanced text extraction and OCR).

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ameer611/AI-Medicine-Remineder.git
   cd AI-Medicine-Remineder
   ```

2. **Configure Environment Variables:**
   Copy the example environment file and fill in your API keys.
   ```bash
   cp .env.example .env
   ```
   Edit `.env` using your preferred text editor:
   - `BOT_TOKEN`: Your Telegram Bot Token.
   - `CEREBRAS_API_KEY`: API Key for extracting schedule duration.
   - `GEMINI_API_KEY`: API Key for Google Gemini (OCR).
   - `DATABASE_URL`: Ensure it points to the docker network (`mysql+aiomysql://dori:secret@mysql:3306/dori_scheduler` for docker-compose).

3. **Run with Docker Compose:**
   Build and start the application in detached mode.
   ```bash
   docker-compose up -d --build
   ```

4. **Verify the services:**
   Ensure all three containers (`dori_mysql`, `dori_api`, `dori_bot`) are running securely mapping data.
   ```bash
   docker-compose ps
   ```

### Running Locally (Without Docker)

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start a local MySQL instance and update the `DATABASE_URL` in `.env` to point to `localhost`.
3. Start the API Server:
   ```bash
   python run_api.py
   ```
4. In a separate terminal, start the Telegram Bot:
   ```bash
   python run_bot.py
   ```

## 💬 Usage (Bot Commands)

- `/start` - Register or log in to the bot and access the main menu.
- `/my_medications` - See your current active medications.
- Send any clear image of a prescription to trigger automatic OCR.
- The bot features interactive inline buttons heavily reliant on callback queries, you usually won't need to type out many commands.
