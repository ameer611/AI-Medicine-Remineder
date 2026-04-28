# Deployment & Operations

Production deployment, configuration, monitoring, and troubleshooting for Dori Scheduler.

**Table of Contents**
- [Docker Compose Deployment](#docker-compose-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Initialization](#database-initialization)
- [Health Checks](#health-checks)
- [Scaling Considerations](#scaling-considerations)
- [Monitoring & Logging](#monitoring--logging)
- [Troubleshooting](#troubleshooting)
- [Backup & Recovery](#backup--recovery)

---

## Docker Compose Deployment

Docker Compose orchestrates three services: MySQL, API, and Bot.

### **Quick Start**

```bash
# Clone and configure
git clone https://github.com/yourusername/dori_scheduler.git
cd dori_scheduler

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Build and start
docker-compose up -d --build

# Verify
docker-compose ps

# View logs
docker-compose logs -f
```

### **docker-compose.yml Structure**

```yaml
services:
  mysql:
    image: mysql:8.0
    container_name: dori_mysql
    # Database configuration
    environment:
      MYSQL_ROOT_PASSWORD: rootsecret
      MYSQL_DATABASE: dori_scheduler
      MYSQL_USER: dori
      MYSQL_PASSWORD: secret
    ports:
      - "3307:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "dori", "-psecret"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: .
    container_name: dori_api
    depends_on:
      mysql:
        condition: service_healthy  # Wait for DB
    env_file:
      - .env
    environment:
      - DATABASE_URL=mysql+aiomysql://dori:secret@mysql:3306/dori_scheduler
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5
    command: python run_api.py

  bot:
    build: .
    container_name: dori_bot
    depends_on:
      mysql:
        condition: service_healthy
      api:
        condition: service_healthy  # Wait for API
    env_file:
      - .env
    environment:
      - DATABASE_URL=mysql+aiomysql://dori:secret@mysql:3306/dori_scheduler
      - API_BASE_URL=http://api:8000  # Internal Docker host
    command: python run_bot.py

volumes:
  mysql_data:
    driver: local
```

### **Service Startup Order**

```
1. MySQL starts
   ↓ (waits for health check)
2. API starts (connects to MySQL)
   ↓ (waits for health check)
3. Bot starts (connects to DB & API)
   ↓ (creates APScheduler jobs)
4. All ready → Reminders can fire
```

### **Common Commands**

```bash
# Start services
docker-compose up -d --build

# Stop services
docker-compose down

# View status
docker-compose ps

# View logs
docker-compose logs -f          # All services
docker-compose logs -f api      # Only API
docker-compose logs -f bot      # Only bot

# Shell into container
docker-compose exec api sh
docker-compose exec mysql mysql -u dori -psecret

# Rebuild image
docker-compose build --no-cache

# Remove volumes (⚠️ clears database)
docker-compose down -v
```

---

## Environment Configuration

### **Required Environment Variables**

```env
# Telegram
BOT_TOKEN=your_telegram_bot_token_from_botfather

# External APIs
GEMINI_API_KEY=your_google_gemini_api_key
GROQ_API_KEY=your_groq_api_key

# Database
DATABASE_URL=mysql+aiomysql://dori:secret@mysql:3306/dori_scheduler

# API Base URL (for bot to call API)
API_BASE_URL=http://api:8000  # Docker
# API_BASE_URL=http://localhost:8000  # Local dev
```

### **Getting API Keys**

#### **Telegram Bot Token**
1. Open Telegram
2. Search for `@BotFather`
3. Send `/newbot`
4. Follow prompts to create bot
5. Copy token (looks like `123456789:ABCDEFGHIjklmnopqrstuvwxyz`)

#### **Google Gemini API Key**
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click "Get API Key"
3. Create new project and generate API key
4. Copy key (looks like `AIza...`)

#### **Groq API Key**
1. Go to [Groq Console](https://console.groq.com/)
2. Sign up/login
3. Create API key in settings
4. Copy key (looks like `gsk_...`)

### **Security Best Practices**

- ✅ **Never commit `.env` file** — Add to `.gitignore`
- ✅ **Use strong DB passwords** — Change from `secret` in production
- ✅ **Rotate API keys regularly** — Set expiration policies
- ✅ **Use secrets management** — Environment variables or Kubernetes secrets
- ✅ **Limit API key scopes** — Restrict to minimal permissions needed

---

## Database Initialization

### **First-Time Setup**

**Automatic (Docker):**
Tables are created automatically on first startup via SQLAlchemy `metadata.create_all()`.

**Manual (Local Dev):**
```bash
python -c "
import asyncio
from app.database import init_db
asyncio.run(init_db())
"
```

### **Schema Creation Order**

SQLAlchemy creates tables in dependency order:
1. `users` (no dependencies)
2. `medications` (references `users`)
3. `schedules` (references `medications`)

### **Verifying Setup**

```bash
# Shell into DB
docker-compose exec mysql mysql -u dori -psecret -D dori_scheduler

# Check tables
SHOW TABLES;
# Output:
# +--------------------------+
# | Tables_in_dori_scheduler |
# +--------------------------+
# | users                    |
# | medications              |
# | schedules                |
# +--------------------------+

# Check users table
DESCRIBE users;
# Output:
# +------------+-----+-----+-----+----------+-------+
# | Field      | Type| ... |     |          | Extra |
# +------------+-----+-----+-----+----------+-------+
# | id         | int | ... |     |          | ...   |
# | telegram_id| +--+ | ... | NO  |          | ...   |
# +------------+-----+-----+-----+----------+-------+
```

### **Pre-Loading Test Data**

Create `scripts/seed_data.py` for development:

```python
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User, Medication, Schedule

async def seed():
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        stmt = select(User)
        result = await session.execute(stmt)
        if result.scalars().first():
            print("Database already has data")
            return
        
        # Create test user
        user = User(telegram_id=123456789)
        session.add(user)
        await session.flush()
        
        # Create test medication
        med = Medication(
            user_id=user.id,
            name="Test Aspirin",
            dosage_per_day=2,
            notes="for testing"
        )
        session.add(med)
        await session.flush()
        
        # Create test schedule
        schedule = Schedule(
            medication_id=med.id,
            time="08:00",
            reminder_offset_minutes=5,
            duration_in_days=7
        )
        session.add(schedule)
        await session.commit()
        
        print("✓ Test data seeded")

if __name__ == "__main__":
    asyncio.run(seed())
```

Run:
```bash
python scripts/seed_data.py
```

---

## Health Checks

### **API Health Endpoint**

```bash
curl http://localhost:8000/health

# Response:
# {"status": "ok"}
```

**Used by:** Docker Compose to verify API is ready before starting bot

### **Bot Health**

The bot doesn't have a health endpoint, but you can verify via Telegram:
```
Send: /start
Expected: Bot responds with main menu
```

### **Database Health**

```bash
# From container
docker-compose exec mysql mysqladmin -u dori -psecret ping

# Expected output:
# mysqld is alive
```

### **Monitoring Health**

```bash
# Watch health status
watch -n 5 'docker-compose ps'

# Or periodic check script
while true; do
  curl -s http://localhost:8000/health | grep -q "ok" && echo "✓ API healthy" || echo "✗ API down"
  sleep 30
done
```

---

## Scaling Considerations

### **Current Architecture Limitations**

| Component | Scale | Limitation |
|-----------|-------|-----------|
| **API** | ✅ Multi-instance | Stateless, can scale horizontally |
| **Bot** | ⚠️ Single instance | In-memory FSM state, APScheduler jobs |
| **Database** | ✅ Vertical scaling | Schema fits in single MySQL instance |
| **APScheduler** | ⚠️ Single bot | Jobs in-memory, lost on restart |

### **For Production Scale (10k+ users)**

**Current Issues:**
- APScheduler jobs stored in-memory
- Single bot instance → single point of failure
- Bot FSM state not persistent

**Solutions:**

1. **Migrate to Celery + Redis**
   ```
   Replace APScheduler with Celery
   - Jobs stored in Redis
   - Multiple bot instances can run
   - Distributed reminder scheduling
   ```

2. **Persistent FSM State**
   ```
   Replace MemoryStorage with Redis storage
   - User state survives bot restarts
   - Easier debugging
   ```

3. **Database Replication**
   ```
   Use MySQL master-slave replication
   - Read from replicas
   - Write to master
   ```

4. **Multiple Bot Instances**
   ```
   With external scheduler:
   - Load balance user connections
   - Auto-restart failed instances
   ```

### **Quick Scaling (Current Architecture)**

**Vertical Scaling:**
- Increase Docker resource limits
- Allocate more CPU/RAM to containers

```yaml
services:
  api:
    ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2048M
        reservations:
          cpus: '1'
          memory: 1024M
```

**Multiple API Instances + Load Balancer:**
```yaml
services:
  api-1:
    build: .
    ports:
      - "8001:8000"
  
  api-2:
    build: .
    ports:
      - "8002:8000"
  
  nginx:
    image: nginx:latest
    ports:
      - "8000:80"
    volumes:
      - nginx.conf:/etc/nginx/nginx.conf
```

---

## Monitoring & Logging

### **Log Output**

**API Logs:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
INFO:app.routers.medications:Saving medication: Aspirin
ERROR:app.services.ocr_service:OCR failed: timeout
```

**Bot Logs:**
```
INFO:root:Starting bot polling...
DEBUG:aiogram.client.session:Request: POST https://api.telegram.org/bot.../getUpdates
INFO:bot.handlers.start:User 123456789 started
ERROR:bot.handlers.image:OCR endpoint returned 502
```

### **Viewing Logs**

```bash
# Real-time logs (all)
docker-compose logs -f --tail=50

# Follow only API
docker-compose logs -f api

# Follow only bot
docker-compose logs -f bot

# Search logs
docker-compose logs | grep ERROR

# Logs with timestamps
docker-compose logs --timestamps
```

### **Structured Logging (Optional)**

```python
import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'module': record.name,
            'message': record.getMessage(),
        }
        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

---

## Troubleshooting

### **Bot Won't Start**

**Symptoms:**
```
ERROR: Service "bot" failed to start
```

**Debugging:**
```bash
# Check logs
docker-compose logs bot

# Common errors:
# - BOT_TOKEN not set → Update .env
# - API not ready → Check API health
# - Database not accessible → Verify DATABASE_URL

# Restart
docker-compose restart bot
```

### **API Returns 502 on /ocr or /parse**

**Cause:** External API failure (Gemini, Groq timeout/rate limit)

**Solution:**
```bash
# Check API keys are correct
echo $GEMINI_API_KEY
echo $GROQ_API_KEY

# Test API directly
curl -X POST http://localhost:8000/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "Aspirin twice daily"}'

# Check error details in logs
docker-compose logs api | tail -20

# If rate limited, wait 60 seconds and retry
```

### **Database Connection Refused**

**Symptoms:**
```
ERROR: Can't connect to MySQL server on 'mysql:3306'
```

**Debugging:**
```bash
# Check MySQL is running
docker-compose ps mysql

# Check health
docker-compose exec mysql mysqladmin -u dori -psecret ping

# Verify password
grep MYSQL_PASSWORD docker-compose.yml

# Check port mapping
docker-compose exec mysql mysql -u dori -psecret -e "SELECT 1"
```

### **Reminders Not Firing**

**Debugging:**
```bash
# Check APScheduler jobs
docker-compose exec bot python -c "
from apscheduler.schedulers.background import BackgroundScheduler
print('APScheduler available')
"

# Check database has schedules
docker-compose exec mysql mysql -u dori -psecret -D dori_scheduler \
  -e "SELECT * FROM schedules LIMIT 5"

# Check bot logs for job creation
docker-compose logs bot | grep -i "scheduler\|job"
```

### **Memory Usage Growing**

**Cause:** Likely APScheduler jobs accumulating in memory

**Solution:**
```bash
# Restart bot to clear in-memory jobs
docker-compose restart bot

# Monitor memory
watch -n 5 'docker stats dori_bot'

# Increase memory limit in docker-compose.yml
```

### **Database Storage Growing Too Fast**

**Cure:** Clean old schedules (after duration expires, records remain)

```sql
-- Remove schedules older than 90 days
DELETE FROM schedules 
WHERE DATE_ADD(created_at, INTERVAL duration_in_days DAY) < NOW();

-- Archive old medications
-- (Implement retention policy based on business needs)
```

---

## Backup & Recovery

### **Automated Backup Script**

Create `scripts/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/dori_DB_$DATE.sql"

# Create backup
docker-compose exec -T mysql mysqldump \
  -u dori -psecret \
  dori_scheduler > "$BACKUP_FILE"

# Compress
gzip "$BACKUP_FILE"

# Keep only last 7 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

echo "✓ Backup saved: $BACKUP_FILE.gz"
```

**Run Backup:**
```bash
chmod +x scripts/backup.sh
./scripts/backup.sh

# Schedule via cron (daily at 2 AM)
0 2 * * * /path/to/dori_scheduler/scripts/backup.sh
```

### **Restore from Backup**

```bash
# Stop services
docker-compose down

# Restore database
gzip -dc backups/dori_db_20240428_020000.sql.gz | \
  docker-compose exec -T mysql mysql -u dori -psecret dori_scheduler

# Restart
docker-compose up -d
```

### **Persistent Volume Backup**

```bash
# Backup MySQL volume
docker run --rm \
  -v dori_scheduler_mysql_data:/data \
  -v /backups:/backup \
  alpine tar czf /backup/mysql_volume_$(date +%Y%m%d).tar.gz -C /data .

# Restore volume
docker run --rm \
  -v dori_scheduler_mysql_data:/data \
  -v /backups:/backup \
  alpine tar xzf /backup/mysql_volume_20240428.tar.gz -C /data
```

---

## Production Checklist

Before deploying to production:

- [ ] Environment variables configured securely
- [ ] Database backups automated (daily)
- [ ] Health checks verified (API, MySQL, Bot)
- [ ] Logging configured and monitored
- [ ] API keys rotated and secured
- [ ] Database passwords changed from defaults
- [ ] API rate limiting implemented (optional)
- [ ] Bot error handling reviewed
- [ ] Monitoring alerts set up (optional)
- [ ] Disaster recovery plan documented
- [ ] Load testing completed (if scaling needed)
- [ ] Security scan completed (secrets, dependencies)

---

## See Also

- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — Local development setup
- [ARCHITECTURE.md](ARCHITECTURE.md) — System design and components
- [DATABASE.md](DATABASE.md) — Schema and data models
- Docker Compose Docs: https://docs.docker.com/compose/

---

**Last Updated:** April 2026  
**Status:** Complete
