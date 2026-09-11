# LUMINA — PRODUCTION DEPLOYMENT GUIDE

## 1. Prerequisites
- Docker & Docker Compose or Bare-metal Linux host (Ubuntu 22.04+ / Debian 12).
- PostgreSQL 15+ database instance.
- Telegram Bot Token from `@BotFather`.
- Registered Domain with SSL/TLS certificate (HTTPS is mandatory for Telegram WebApps).

## 2. Environment Configuration
Create production `.env` (never commit to git):
```env
ENV=production
DEBUG=false
APP_URL=https://lumina-green-nine.vercel.app
API_PREFIX=/api/v1

DATABASE_URL=postgresql+asyncpg://lumina_user:StrongPassword@localhost:5432/lumina_db
JWT_SECRET=super_secret_high_entropy_random_key_min_32_bytes
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz
TELEGRAM_WEBHOOK_URL=https://lumina-green-nine.vercel.app/api/v1/webhook
TELEGRAM_WEBHOOK_SECRET=cryptographic_webhook_secret_header

CORS_ORIGINS=["https://lumina-green-nine.vercel.app","https://web.telegram.org"]
```

## 3. Database Initialization & Migrations
```bash
# Apply migrations
alembic upgrade head

# Run automated tests to verify clean install
python -m pytest -v
```

## 4. Launch Services
```bash
# Start API server with Uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Start Telegram Bot Polling (or configure webhook)
python bot/main.py
```

## 5. Vercel Serverless Production Deployment
```bash
vercel deploy --prod --yes
```
Production URL: `https://lumina-green-nine.vercel.app`
