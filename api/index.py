"""Vercel Serverless ASGI Entrypoint for Lumina FastAPI application."""

from api.main import app

# Expose app for Vercel Serverless runtime
__all__ = ["app"]
