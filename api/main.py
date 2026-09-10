"""Main FastAPI Application entrypoint for Lumina Telegram School OS."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers import admin, auth, parent, shared, student, teacher
from db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database schema on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Lumina — Telegram School OS API",
    description="High-performance, secure backend for Lumina Telegram School Operating System.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for Telegram Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under /api/v1
api_v1_prefix = "/api/v1"
app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(shared.router, prefix=api_v1_prefix)
app.include_router(admin.router, prefix=api_v1_prefix)
app.include_router(teacher.router, prefix=api_v1_prefix)
app.include_router(student.router, prefix=api_v1_prefix)
app.include_router(parent.router, prefix=api_v1_prefix)


from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Mount static webapp
webapp_dir = Path(__file__).parent.parent / "webapp"
if webapp_dir.exists():
    app.mount("/app", StaticFiles(directory=str(webapp_dir), html=True), name="webapp")


@app.get("/")
async def root():
    return {
        "app": "Lumina — Telegram School OS",
        "version": "1.0.0",
        "webapp": "/app",
        "docs": "/docs",
        "health": "/health",
        "ping": "/ping",
    }


@app.get("/health", tags=["Monitoring"])
async def health_check_uptimerobot():
    """UptimeRobot HTTP(s) Monitor endpoint. Returns 200 OK."""
    return {
        "status": "healthy",
        "service": "Lumina School OS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ping", tags=["Monitoring"])
async def ping_uptimerobot():
    """Lightweight ping endpoint returning keyword PONG for keyword monitoring."""
    return "PONG"
