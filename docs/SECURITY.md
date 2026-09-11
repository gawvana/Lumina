# LUMINA — SECURITY & MULTI-TENANT ISOLATION SPECIFICATION

## 1. Multi-Tenant School Isolation Policy
- Every database entity (Users, Classes, Subjects, Lessons, Grades, Attendance, Homework, Files, Invites, Audit Logs) enforces strict server-side `school_id` scoping.
- Client-side parameters cannot override tenancy: `current_user.school_id` extracted from cryptographically verified JWT tokens is unconditionally enforced across all database queries.
- Cross-school operations (e.g. Teacher from School A querying Students or grading Lessons in School B) return HTTP 403 / 404.

## 2. Authentication & Cryptography
- **Telegram Mini App Verification**:
  - Validates `initData` using HMAC-SHA256 with the secret key derived from `WebAppData` and Bot Token.
  - Enforces replay protection and `auth_date` expiration ($\le 24$ hours).
  - Production environments reject tampered hash, expired initData, or unauthorized webviews.
- **JWT Architecture**:
  - Signed using HS256/Ed25519 with cryptographically secure secret keys (`JWT_SECRET`).
  - Strict expiration (Access Token: 60 minutes, Refresh Token: 30 days).
  - Dev-tokens and debug role bypasses are strictly disabled in production (`ENV != "development"`).

## 3. Cryptographic Invite System
- Invites are single-use or count-capped with cryptographically generated tokens (`inv_` + 32-byte URL-safe base64).
- Bound to specific `school_id`, `role`, and optional `class_id`.
- Automatically invalidated upon expiration or explicit administrator revocation.

## 4. Immutable Audit Trail
- Critical state mutations (grade creation, grade correction, grade undo deletion, attendance changes, user permission updates) create non-deletable records in `audit_logs` containing `actor_id`, `school_id`, `action`, `old_values`, `new_values`, and `created_at`.

## 5. Security Headers & CORS
- Strict CORS configuration in production prohibiting open wildcards (`*`) for authenticated endpoints.
- `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, and `X-Frame-Options` allowing embedding strictly inside Telegram WebViews.
