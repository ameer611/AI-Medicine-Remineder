# Dori Scheduler - Documentation Hub

Welcome! This documentation package provides comprehensive guides for developers, operators, and users of the **Dori Scheduler** medication reminder system.

## 📚 Documentation Overview

Choose a guide based on your role and needs:

### **For Developers Onboarding**

Start here to understand the system architecture and set up your development environment:

1. **[ARCHITECTURE.md](ARCHITECTURE.md)** — System design, component responsibilities, data flows, and technology stack overview
   - Understand how the bot, API, database, and external services fit together
   - Visualize data flows from prescription scanning to reminder delivery

2. **[DATABASE.md](DATABASE.md)** — Complete database schema, models, relationships, and repository patterns
   - Learn the User → Medication → Schedule data model
   - Understand cascade deletes and foreign key relationships
   - Study the abstract repository layer

3. **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** — Local setup, project structure, coding patterns, and extending the codebase
   - Set up your dev environment (Python, MySQL, Docker)
   - Understand folder organization and module responsibilities
   - Learn patterns for adding new endpoints or bot handlers

### **For API Integration**

Using the Dori Scheduler backend in your application?

4. **[API_REFERENCE.md](API_REFERENCE.md)** — Complete API endpoint reference with request/response examples
   - All endpoints: `/ocr`, `/parse`, `/medications`
   - Request/response schemas with real examples
   - Error codes and handling
   - cURL and Python code samples

### **For Bot Interface**

Managing or debugging the Telegram bot?

5. **[BOT_COMMANDS.md](BOT_COMMANDS.md)** — Telegram bot commands, FSM states, handlers, and user interactions
   - All available commands: `/start`, `/my_medications`
   - State machine flow with diagrams
   - Handler descriptions and keyboard layouts
   - User interaction workflows

6. **[USER_GUIDE.md](USER_GUIDE.md)** — End-user guide: how to use the bot effectively
   - Step-by-step: scanning a prescription
   - Manually adding a medication
   - Viewing and managing schedules
   - FAQs and common issues

### **For Deployment & Operations**

Deploying to production or troubleshooting?

7. **[DEPLOYMENT.md](DEPLOYMENT.md)** — Deployment, configuration, monitoring, and operations
   - Docker Compose setup and execution
   - Environment variables and configuration
   - Database initialization and migrations
   - Health checks and monitoring
   - Troubleshooting deployment issues

---

## 🎯 Quick Navigation

| Role | Start With | Then Read |
|------|-----------|-----------|
| **New Developer** | [ARCHITECTURE.md](ARCHITECTURE.md) | → [DATABASE.md](DATABASE.md) → [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) |
| **API Consumer** | [API_REFERENCE.md](API_REFERENCE.md) | — |
| **Bot Maintainer** | [BOT_COMMANDS.md](BOT_COMMANDS.md) | → [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) |
| **Operations/DevOps** | [DEPLOYMENT.md](DEPLOYMENT.md) | → [ARCHITECTURE.md](ARCHITECTURE.md) |
| **End User** | [USER_GUIDE.md](USER_GUIDE.md) | — |

---

## 📋 Project Summary

**Dori Scheduler** is a production-grade medication reminder system combining:

- 🎙️ **Telegram Bot Interface** — Interactive bot using Aiogram 3.x
- 🔌 **FastAPI Backend** — REST API with async/await architecture
- 🗄️ **MySQL Database** — User, medication, and schedule management with SQLAlchemy ORM
- 🤖 **AI Integration** — LLM-powered prescription parsing (Groq), OCR (Gemini Vision)
- ⏲️ **Task Scheduling** — APScheduler for automated daily reminders
- 🐳 **Containerized** — Full Docker Compose setup for development and production

---

## 🚀 Quick Start

### **Via Docker Compose (Recommended)**

```bash
# Clone the repo
git clone <repo-url>
cd dori_scheduler

# Configure environment
cp .env.example .env
# Edit .env with your API keys (BOT_TOKEN, GEMINI_API_KEY, GROQ_API_KEY)

# Start all services
docker-compose up -d --build

# Verify services are running
docker-compose ps
```

All three services (MySQL, API, Bot) will start automatically with health checks.

### **Local Development**

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#local-development-setup) for step-by-step instructions on running the API and bot locally.

---

## 📞 Troubleshooting

- **Bot won't start?** → See [DEPLOYMENT.md - Troubleshooting](DEPLOYMENT.md#troubleshooting)
- **API returning errors?** → Check [API_REFERENCE.md - Error Handling](API_REFERENCE.md#error-handling)
- **Database connection issues?** → Review [DEPLOYMENT.md - Database Initialization](DEPLOYMENT.md#database-initialization)
- **Want to modify a feature?** → Start with [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)

---

## 📄 Document Status

- ✅ **ARCHITECTURE.md** — Complete system design and data flows
- ✅ **DATABASE.md** — Full schema documentation with ER diagrams
- ✅ **API_REFERENCE.md** — All endpoints with examples and error codes
- ✅ **BOT_COMMANDS.md** — Commands, states, handlers with workflows
- ✅ **USER_GUIDE.md** — End-user instructions and FAQs
- ✅ **DEVELOPER_GUIDE.md** — Development setup and codebase patterns
- ✅ **DEPLOYMENT.md** — Production deployment and operations

---

## 🔗 Document Cross-References

Every document includes:
- **See Also** section with related docs
- **Internal links** to specific sections
- **Code references** to relevant source files

Use these to navigate between related topics.

---

## 📝 Notes for Contributors

When updating documentation:
1. Keep examples current with actual code
2. Maintain consistent formatting and structure
3. Update cross-links when changing document titles/sections
4. Test all code samples and commands before committing

---

**Last Updated:** April 2026  
**Version:** 1.0  
**Status:** Comprehensive documentation complete
