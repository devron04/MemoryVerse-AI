"""
MemoryVerse AI — FastAPI Entrypoint

Main application with CORS middleware, route registration,
and startup hooks for directory creation.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, ensure_directories
from app.api import upload, documents, search, chat, graph, timeline, career

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Runs setup on startup and cleanup on shutdown.
    """
    logger.info("Starting MemoryVerse AI backend...")
    try:
        settings = get_settings()
        ensure_directories(settings)
        logger.info("Upload directory: %s", settings.upload_dir)
        logger.info("Data directory: %s", settings.data_dir)
        logger.info("LLM model: %s", settings.gemini_model)
    except Exception as e:
        logger.error("Failed to initialize: %s", str(e))
        raise

    yield

    logger.info("Shutting down MemoryVerse AI backend...")


app = FastAPI(
    title="MemoryVerse AI",
    description="Living Digital Identity System — upload documents, extract metadata, "
                "build a knowledge graph, and discover career insights.",
    version="0.3.0 (Phase 3)",
    lifespan=lifespan,
)

# CORS middleware — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(upload.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(timeline.router, prefix="/api")
app.include_router(career.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "phase": "Phase 3 — Retrieval & Semantic Chat Search"}
