# Lumina — Autonomous Engineering Decisions Log

This document records the design and architectural choices made autonomously during the development of Lumina School OS, in accordance with Section 0, Rule 6 of the Build Brief.

---

### Decision 01: Multi-Tenant Single Database Architecture
* **Context**: Need to support multiple independent schools while maintaining strict data isolation.
* **Choice**: Single database with `school_id` foreign key on all organizational and academic tables.
* **Rationale**: Optimal operational simplicity, fast provisioning of new schools, single Alembic migration runner, and shared asyncio connection pool.
* **Security Enforcement**: `verify_school_isolation(current_user, target_school_id)` runs in dependencies and service layers. Even if an attacker tampers with an entity ID, mismatch with `current_user.school_id` triggers `403 Forbidden`.

---

### Decision 02: Telegram WebApp `initData` Cryptographic Authentication
* **Context**: The Telegram Mini App communicates with the backend via REST API.
* **Choice**: Server-side HMAC-SHA256 signature verification against `TELEGRAM_BOT_TOKEN` followed by issuance of a signed JWT token with a 7-day expiration.
* **Rationale**: Eliminates client-side trust. Validates `auth_date` to prevent replay attacks.

---

### Decision 03: Grade Immutability and Audit Lineage (Second Chance)
* **Context**: Teachers need to correct grades (Second Chance), but school systems require tamper-proof audit trails.
* **Choice**: Physical deletion of grades is prohibited. When a grade is updated, the active row is modified, `is_retake` is set, and a complete snapshot of both `old_values` and `new_values` is permanently logged into `audit_logs`.
* **Rationale**: Protects institutional integrity and enables retrospective dispute resolution.

---

### Decision 04: Per-School Feature Flags with Default OFF
* **Context**: Features from Phase 2–5 (AI assistance, voice grading, vibe tracking, leaderboard) must not destabilize core operations.
* **Choice**: `feature_flags` database table per school, seeded with all Phase 2–5 features disabled (`is_enabled: false`).
* **Rationale**: Allows administrators to toggle capabilities on demand without code changes or restarts.

---

### Decision 05: Unified i18n Dictionary Engine (Russian & Uzbek)
* **Context**: System must support Russian and Uzbek from Day 1 without hardcoded strings in code.
* **Choice**: Centralized JSON dictionary files in `locales/ru.json` and `locales/uz.json`.
* **Rationale**: The same dictionaries power backend error messages, bot push notifications, and the Mini App frontend via `/api/v1/shared/locales/{lang}`.

---

### Decision 06: Zero-Dependency Pure Python Search for Design & UI/UX
* **Context**: Need high-speed design intelligence lookup without external npm or pip bloat.
* **Choice**: Integrated `ui-ux-pro-max` search script via pure standard-library Python (BM25 + regex).
* **Rationale**: Reliable, instant lookup for design tokens, font pairings, and color palettes on all operating systems.
