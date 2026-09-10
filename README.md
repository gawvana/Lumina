# Lumina — Telegram School OS

Lumina — школьная операционная система внутри Telegram, сочетающая высокоскоростной push-канал (Telegram Bot) и рабочее пространство (Telegram Mini App).

---

## 🛠 Технологический стек

* **Бэкенд**: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Alembic
* **База данных**: SQLite (`aiosqlite`) для локальной разработки, PostgreSQL (`asyncpg`) для продакшена
* **Бот**: aiogram 3.x, asyncio
* **Фронтенд Mini App**: Modern Vanilla HTML/CSS/JS + Telegram WebApp SDK + Lucide Icons
* **Безопасность**: Серверная валидация `initData` по алгоритму HMAC-SHA256, RBAC-контроль, изоляция школ, Audit Log

---

## 📁 Структура проекта

```text
lumina/
├── bot/                 # aiogram 3.x: обработчики, deep-link инвайты, запуск
├── api/                 # FastAPI REST API: роутеры, сервисы, RBAC middleware
├── webapp/              # Telegram Mini App (5 разделов на роль, ru/uz, темная тема)
├── db/                  # SQLAlchemy 2.0 Async модели и управление сессиями
├── shared/              # Общие enum'ы, i18n хелперы, HMAC-SHA256 валидация
├── locales/             # Локализационные словари (ru.json, uz.json)
├── tests/               # Pytest набор тестов на безопасность, RBAC и аудит
└── docs/
    └── decisions.md     # Лог архитектурных решений
```

---

## 🚀 Быстрый старт

### 1. Запуск тестов безопасности (RBAC, аудит, инвайты, HMAC)
```bash
python -m pytest tests/ -v
```

### 2. Запуск REST API и WebApp сервера
```bash
uvicorn api.main:app --reload --port 8000
```
* Документация Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
* Telegram Mini App: [http://localhost:8000/app/](http://localhost:8000/app/)

### 3. Запуск Telegram Бота
Укажите ваш `TELEGRAM_BOT_TOKEN` в `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
WEBAPP_URL=https://your-domain.com/app/
```
И запустите бота:
```bash
python -m bot.main
```
