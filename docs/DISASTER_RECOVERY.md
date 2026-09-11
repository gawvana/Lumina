# LUMINA — DISASTER RECOVERY & INCIDENT PLAYBOOK

## 1. PostgreSQL Database Recovery
1. **Automated Backups**: Nightly compressed binary dumps (`pg_dump -Fc`) stored in encrypted object storage with 30-day retention.
2. **Point-in-Time Restore**:
   ```bash
   pg_restore -h $DB_HOST -U $DB_USER -d lumina_prod --clean --if-exists lumina_backup_latest.dump
   ```
3. **Integrity Validation**: Run the automated test suite against the restored database to verify foreign key integrity:
   ```bash
   python -m pytest tests/test_features_correctness.py tests/test_rbac.py
   ```

## 2. Secret Compromise & Rotation
If `BOT_TOKEN`, `JWT_SECRET`, or database credentials are leaked:
1. Revoke the token via Telegram `@BotFather` (`/revoke`).
2. Update `.env` / Vercel Environment Variables with newly generated secrets:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
3. Redeploy API and Bot containers. All existing JWT sessions will be invalidated, prompting seamless re-authentication via Telegram WebApp `initData`.

## 3. Webhook Outage & Re-registration
If Telegram updates fail to arrive:
1. Verify endpoint health:
   ```bash
   curl -s https://api.lumina.uz/health
   ```
2. Re-register webhook with secret token:
   ```bash
   curl -F "url=https://api.lumina.uz/api/v1/webhook" \
        -F "secret_token=$TELEGRAM_WEBHOOK_SECRET" \
        https://api.telegram.org/bot$BOT_TOKEN/setWebhook
   ```
