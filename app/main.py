"""
FastAPI Application Entry Point.
Production-ready with rate limiting, CORS, exception handling, and lifespan management.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.config import get_settings
from core.database import init_db
from core.logging_config import setup_logging

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting Persona AI Chatbot...")
    logger.info(f"LLM Model: {settings.LLM_MODEL}")
    logger.info(f"ChromaDB path: {settings.CHROMA_PERSIST_DIR}")

    # Initialize database tables
    await init_db()
    logger.info("✅ Database initialized")

    # Pre-load persona config
    from personas.persona_service import get_all_personas
    personas = get_all_personas()
    logger.info(f"✅ Loaded {len(personas)} personas")

    yield

    # Shutdown
    logger.info("👋 Shutting down Persona AI Chatbot...")


# Create FastAPI app
app = FastAPI(
    title="Persona AI Chatbot",
    description="Production-ready AI chatbot with multi-persona support, memory isolation, and onboarding.",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal error occurred. Please try again.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# Include routers
from routes.onboarding_routes import router as onboarding_router
from routes.persona_routes import router as persona_router
from routes.chat_routes import router as chat_router
from routes.memory_routes import router as memory_router
from routes.health_routes import router as health_router

app.include_router(onboarding_router)
app.include_router(persona_router)
app.include_router(chat_router)
app.include_router(memory_router)
app.include_router(health_router)


from fastapi.staticfiles import StaticFiles
app.mount("/frontend", StaticFiles(directory="../frontend"), name="frontend")

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "Persona AI Chatbot",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "personas": "/personas",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
