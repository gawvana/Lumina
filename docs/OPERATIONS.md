# LUMINA — SRE & OPERATIONS MANUAL

## 1. Health Monitoring & Observability
- `/api/v1/shared/health`: Returns HTTP 200 `{"status": "ok", "service": "Lumina School OS"}`.
- Structured logging using Python `logging` with JSON/formatted records, automatically sanitizing passwords, tokens, and Telegram raw initData strings.

## 2. Key Operational Metrics
- **Database Connection Pool**: Alert when active connections exceed 80% of `pool_size`.
- **API Latency**: $p95 \le 120$ms for student dashboards and grade queries.
- **Telegram Update Processing**: Ensure Webhook responses return HTTP 200 within 1500ms to avoid Telegram retry storms.

## 3. Routine Maintenance
- **Weekly Inactive Session Pruning**: Delete expired refresh tokens and single-use invites older than 7 days.
- **Audit Log Retention**: Retain audit records for a minimum of 3 academic years for compliance and dispute resolution.
