# Lumina — Telegram School OS

Lumina — современная коммерческая школьная операционная система внутри Telegram, сочетающая защищённый push-канал (Telegram Bot) и рабочее пространство с Apple-grade интерфейсом (Telegram Mini App).

Платформа спроектирована для полноценной многопользовательской работы школ в реальном продакшене.

---

## 🛠 Технологический стек

* **Бэкенд**: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (AsyncIO), Alembic
* **База данных**: PostgreSQL (`asyncpg`) для продакшена, SQLite (`aiosqlite`) для локальных тестов
* **Telegram Бот**: aiogram 3.x, FSM, Webhook с криптографическим секретным заголовком
* **Фронтенд Mini App**: Modern Vanilla HTML5 / ES Modules / CSS System Tokens + Telegram WebApp SDK + Lucide Icons
* **ИИ-ассистент**: Адаптивные подсказки (сократический метод), подготовка к тестам, умная недельная сводка для родителей с защитой от сбоев (offline fallback)
* **Безопасность**: Серверная валидация `initData` по алгоритму HMAC-SHA256, изоляция тенантов (`school_id`), неизменяемый журнал аудита (`audit_logs`), криптографические инвайты

---

## 📁 Структура проекта

```text
lumina/
├── bot/                 # aiogram 3.x: обработчики, deep-link инвайты, команды
├── api/                 # FastAPI REST API: роутеры, сервисы, RBAC зависимости
│   ├── routers/         # student, teacher, parent, admin, seating, gamification, ai, backpack
│   └── services/        # grade_service, seating_service, xp_service, ai_service, file_service
├── webapp/              # Telegram Mini App (Apple-grade дизайн, ru/uz, темная тема)
│   ├── css/             # main.css, variables.css, components.css
│   └── js/              # app.js, api.js, i18n.js, views/ (student, teacher, parent, admin)
├── db/                  # SQLAlchemy 2.0 Async модели и управление сессиями
├── shared/              # Безопасность, HMAC-SHA256, JWT, i18n хелперы
├── locales/             # Локализационные словари (ru.json, uz.json)
├── tests/               # 33 автоматизированных теста (RBAC, тенанты, геймификация, рассадка, ИИ)
└── docs/                # Производственная документация
    ├── ARCHITECTURE.md
    ├── SECURITY.md
    ├── RBAC_MATRIX.md
    ├── PRODUCTION_AUDIT.md
    ├── GPT_SOURCE_RECONCILIATION.md
    ├── DESIGN_AUDIT.md
    ├── DISASTER_RECOVERY.md
    ├── DEPLOYMENT.md
    ├── OPERATIONS.md
    └── FINAL_AUDIT.md
```

---

## 🚀 Запуск и тестирование

### 1. Запуск автоматизированного тестового набора (33 теста)
```bash
python -m pytest -v
```
Все 33 теста проверяют безопасность, изоляцию школ, ролевые права (RBAC), геймификацию, рассадку парт, отмену оценок и ИИ.

### 2. Запуск локального API и WebApp сервера
```bash
uvicorn api.main:app --reload --port 8000
```
* Swagger API документация: [http://localhost:8000/docs](http://localhost:8000/docs)
* Telegram Mini App: [http://localhost:8000/app/](http://localhost:8000/app/)

### 3. Запуск Telegram Бота
```bash
python -m bot.main
```

### 4. Продакшен деплой (Vercel)
```bash
vercel deploy --prod --yes
```
* Продакшен URL: `https://lumina-green-nine.vercel.app`
