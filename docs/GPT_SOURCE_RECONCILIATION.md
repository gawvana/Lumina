# Lumina — GPT ↔ Source Reconciliation Matrix

**Document Reference**: `docs/GPT_SOURCE_RECONCILIATION.md`  
**Date**: September 2026  
**Methodology**: Rigorous verification against actual code in repository (`db/`, `api/`, `bot/`, `webapp/`, `tests/`).

---

## 1. Feature Reconciliation Table

| Feature | GPT Requirement | Source Evidence | Database | Backend | API | Frontend | Bot | Tests | Status | Missing |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Telegram HMAC Auth** | Verify initData server-side, replay protection | `api/services/auth_service.py` | `users` | Implemented | `/auth/telegram-webapp` | `api.authenticateTelegram` | Webhook setup | `test_init_data.py` | `FULLY_IMPLEMENTED` | None |
| **Multi-Tenant RBAC** | Enforce school isolation server-side | `api/dependencies.py` | `schools`, `users` | Implemented | All protected routes | Role badge + routing | Role check | `test_rbac.py`, `test_security_tenant.py` | `FULLY_IMPLEMENTED` | None |
| **Academic Core (Classes/Subjects)** | Create/view classes & subjects | `api/routers/admin.py` | `classes`, `subjects` | Implemented | `/admin/classes`, `/admin/subjects` | Admin classes view | - | `test_features_correctness.py` | `FULLY_IMPLEMENTED` | None |
| **Curriculum Assignment** | Link teacher to subject & class | `api/routers/admin.py` | `teacher_subject_classes` | Implemented | `/admin/curriculum` | Admin assignment list | - | `test_features_correctness.py` | `FULLY_IMPLEMENTED` | None |
| **Schedule / Lessons** | View daily schedule with rooms | `api/routers/student.py`, `teacher.py` | `lessons` | Implemented | `/student/schedule`, `/teacher/schedule` | Schedule calendar view | `/schedule` | `test_features_correctness.py` | `FULLY_IMPLEMENTED` | Active lesson live highlight |
| **Grades & GPA** | Award grades, calculate GPA | `api/routers/teacher.py`, `student.py` | `grades`, `grading_systems` | Implemented | `/teacher/grades`, `/student/grades` | Grades list + GPA badge | `/grades` | `test_grades_audit.py` | `FULLY_IMPLEMENTED` | Grade weights config |
| **Grade History & Second Chance** | Immutable audit of grade retakes | `api/routers/teacher.py`, `db/models/grading.py` | `grade_history`, `audit_logs` | Implemented | Retake patch endpoint | Retake tag displayed | - | `test_grades_audit.py` | `FULLY_IMPLEMENTED` | 5-min quick undo token |
| **Attendance Tracking** | Present, Absent, Late, Excused | `api/routers/teacher.py`, `student.py` | `attendance` | Implemented | `/teacher/attendance` | Teacher attendance matrix | - | `test_features_correctness.py` | `FULLY_IMPLEMENTED` | None |
| **Parent Child Linking & Absence** | View children marks, submit absence notes | `api/routers/parent.py` | `parents`, `student_parents`, `absence_notes` | Implemented | `/parent/children`, `/parent/absence-notes` | Parent dashboard + note modal | - | `test_features_correctness.py` | `FULLY_IMPLEMENTED` | PDF portfolio export |
| **Invite Tokens** | Scoped, expiring, single-use invites | `api/services/invite_service.py` | `invites` | Implemented | `/admin/invites`, `/auth/redeem-invite` | In-app invite input + link copy | `/start inv_...` | `test_invites.py` | `FULLY_IMPLEMENTED` | None |
| **Feature Flags** | Per-school module toggles | `db/models/feature_flag.py`, `api/routers/admin.py` | `feature_flags` | Implemented | `/admin/feature-flags` | Admin flags list | - | `test_security_tenant.py` | `FULLY_IMPLEMENTED` | None |
| **RU / UZ Localization** | Full 2-language dictionary | `locales/ru.json`, `locales/uz.json` | - | Implemented | `/shared/locales/{lang}` | Dynamic language switch | Multilingual strings | UI test | `FULLY_IMPLEMENTED` | None |
| **XP & Level Ledger** | Auditable XP transactions & level curves | `db/models/gamification.py` | Needed | Planned | Needed | Needed | - | Needed | `SCAFFOLDING_ONLY` | Needs table, service, UI |
| **Daily Learning Streak** | Activity streaks with timezone rules | `db/models/gamification.py` | Needed | Planned | Needed | Needed | - | Needed | `SCAFFOLDING_ONLY` | Needs table, calculation, UI |
| **Achievements & Badges** | Unlocking awards on academic events | `db/models/gamification.py` | Needed | Planned | Needed | Needed | - | Needed | `SCAFFOLDING_ONLY` | Needs engine, icons, UI |
| **Vibe Tracking** | Daily learning mood / vibe selector | `db/models/gamification.py` | Needed | Planned | Needed | Needed | - | Needed | `SCAFFOLDING_ONLY` | Needs model, endpoint, UI |
| **Interactive Seating Chart** | Drag/tap classroom desk layout & student picker | `db/models/seating.py` | Needed | Planned | Needed | Needed | - | Needed | `SCAFFOLDING_ONLY` | Needs grid model, UI sheet |
| **Random Student Picker** | Fair student picker (all/present) | `api/services/seating_service.py` | Needed | Planned | Needed | Needed | - | Needed | `SCAFFOLDING_ONLY` | Needs endpoint, modal |
| **Swipe & Quick Grading Drawer** | Bottom sheet for single-tap grading & notes | `webapp/js/components/sheet.js` | - | Planned | Needed | Needed | - | Needed | `PARTIAL` | Needs bottom sheet component |
| **Flashcards (Spaced Repetition)** | Subject flashcard sets for self-study | `db/models/study.py` | Needed | Planned | Needed | Needed | - | Needed | `NOT_IMPLEMENTED` | Needs model, study runner |
| **Skill Tree (Mastery Curriculum)** | Subject skill progression prerequisites | `db/models/study.py` | Needed | Planned | Needed | Needed | - | Needed | `NOT_IMPLEMENTED` | Needs graph model, UI tree |
| **Digital Backpack (File Storage)** | Secure educational file storage & downloads | `db/models/file.py` | Needed | Planned | Needed | Needed | - | Needed | `NOT_IMPLEMENTED` | Needs model, upload route |
| **AI Study Assistant & Pre-Test Recap** | Adaptive hints & concise review generation | `api/services/ai_service.py` | - | Planned | Needed | Needed | - | Needed | `SCAFFOLDING_ONLY` | Needs service with fallback |
| **Parent Smart Weekly Summary** | Aggregated weekly pulse & attendance digest | `api/services/ai_service.py` | - | Planned | Needed | Needed | - | Needed | `SCAFFOLDING_ONLY` | Needs aggregation & AI summary |
| **Telegram Bot Full Commands** | `/app`, `/grades`, `/homework`, `/schedule`, `/help` | `bot/handlers/commands.py` | - | Planned | Needed | - | Implemented /start | Needed | `PARTIAL` | Additional command handlers |
| **Apple-Level Design System** | Zinc palettes, 44px tap targets, bottom sheets | `webapp/css/` | - | - | - | Needs elevation tokens | - | - | `PARTIAL` | Editorial hierarchy, sheets |

---

## 2. Priority Implementation Roadmap

1. **Step 1 (DB & Models)**: Implement `gamification.py`, `seating.py`, `study.py`, and `file.py` in `db/models/`, register in `db/models/__init__.py`, and generate Alembic migration.
2. **Step 2 (Service Layer)**: Build `XPService`, `SeatingService`, `AIService`, and `FileService` with strict multi-tenant validation and graceful degradation.
3. **Step 3 (API Routers)**: Add `api/routers/gamification.py`, `seating.py`, `backpack.py`, and `ai.py` with standard error contract.
4. **Step 4 (Apple UI/UX & TMA)**: Overhaul `variables.css`, `components.css`, and views to support bottom sheets, segmented controls, touch cards, and new tabs.
5. **Step 5 (Bot Commands)**: Add handlers for `/app`, `/grades`, `/homework`, `/schedule`, `/settings`, `/help`.
6. **Step 6 (Testing & QA)**: Add unit, integration, and security tests in `tests/`, verify with `pytest`.
