"""Main FastAPI Application entrypoint for Lumina Telegram School OS."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.routers import admin, auth, bot_webhook, parent, shared, student, teacher
from db.session import init_db
from shared.config import settings

logger = logging.getLogger("lumina.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initializes DB schema in development / serverless mode."""
    if settings.ENVIRONMENT == "development" or ("sqlite" in settings.DATABASE_URL and "/tmp/" in settings.DATABASE_URL):
        try:
            import shutil
            from pathlib import Path
            src = Path("./lumina.db")
            dst = Path("/tmp/lumina.db")
            if src.exists() and not dst.exists():
                try:
                    shutil.copy2(src, dst)
                except Exception as e:
                    logger.warning("Could not copy lumina.db to /tmp: %s", e)
            await init_db()
            logger.info("Database schema initialized.")
        except Exception as exc:
            logger.warning("init_db encountered an issue: %s", exc)
    yield


app = FastAPI(
    title="Lumina — Telegram School OS API",
    description="High-performance, secure backend for Lumina Telegram School Operating System.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration: strict allowed origins
origins = settings.ALLOWED_ORIGINS
allow_all = "*" in origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if not allow_all else ["*"],
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Global exception handler to prevent internal tracebacks or secrets leaking."""
    logger.error("Unhandled exception at %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred. Please try again later."},
    )


# Include API Routers under /api/v1
api_v1_prefix = "/api/v1"
app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(shared.router, prefix=api_v1_prefix)
app.include_router(admin.router, prefix=api_v1_prefix)
app.include_router(teacher.router, prefix=api_v1_prefix)
app.include_router(student.router, prefix=api_v1_prefix)
app.include_router(parent.router, prefix=api_v1_prefix)
app.include_router(bot_webhook.router, prefix=api_v1_prefix)

# Mount static webapp
webapp_dir = Path(__file__).parent.parent / "webapp"
if webapp_dir.exists():
    app.mount("/app", StaticFiles(directory=str(webapp_dir), html=True), name="webapp")


@app.get("/")
async def root():
    return {
        "app": "Lumina — Telegram School OS",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "webapp": "/app",
        "docs": "/docs",
        "health": "/health",
        "ping": "/ping",
    }


@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Health check endpoint for monitoring uptime and readiness."""
    return {
        "status": "healthy",
        "service": "Lumina School OS",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ping", tags=["Monitoring"])
async def ping():
    """Lightweight ping endpoint returning keyword PONG."""
    return "PONG"
