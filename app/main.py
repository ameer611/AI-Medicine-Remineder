"""FastAPI application entry point."""
import logging

from fastapi import FastAPI

from app.database import create_tables
from app.logging_config import setup_logging
from app.routers import medications, ocr, parse

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Dori Scheduler API",
    description="Smart Prescription → Medication Reminder backend",
    version="1.0.0",
)

app.include_router(ocr.router)
app.include_router(parse.router)
app.include_router(medications.router)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Starting up — creating database tables...")
    await create_tables()


@app.get("/health", tags=["Health"])
async def health() -> dict:
    return {"status": "ok"}
