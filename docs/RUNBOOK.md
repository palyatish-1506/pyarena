# PyArena Runbook

Operational guide for quiz nights and incidents. Keep this open during events.

## Quiz-night checklist (T-30 min)

1. **Health check** — `curl https://pyarena-api.onrender.com/api/v1/health/` → `{"status":"ok","db":"up"}`
2. **Cold start** — Render free tier sleeps; hit `/health/` 2× to warm (~30s).
3. **Login smoke** — log in as a test student on https://pyarena-indol.vercel.app.
4. **Leaderboard check** — `/leaderboard` loads, shows your rank.
5. **Submit smoke** — answer one question, confirm XP + explanation appear.
6. **Sentry check** — no new unresolved issues in the last hour.
7. **Have ready:** admin login, this runbook, Render + Vercel dashboards.

## Rollback

- **Frontend:** Vercel → Deployments → previous deployment → "Promote to Production".
- **Backend:** Render → Events → find last good deploy → "Rollback" (or redeploy previous commit).
- Migrations are backward-compatible by convention — avoid destructive schema changes without a plan.

## Backup & restore (C4)

- **Provider backups:** Render Postgres includes automatic daily backups (Dashboard → your Postgres → Backups). Retention per plan.
- **Manual dump (before risky ops):**
  ```powershell
  $env:DATABASE_URL="<render external db url>"
  pg_dump $env:DATABASE_URL -f backup-$(Get-Date -Format yyyyMMdd).sql
  ```
- **Restore drill (performed 2025-11-24):**
  1. Created `pyarena` local DB from latest Render dump via `pg_restore`.
  2. Ran `manage.py migrate --check` → no pending migrations.
  3. `manage.py shell -c "from django.contrib.auth import get_user_model; print(get_user_model().objects.count())"` → user count matched prod (sanity check).
  4. Result: **restore verified in ~4 minutes**. Repeat quarterly.

## Reading Sentry

- Backend DSN → Render env `SENTRY_DSN`; frontend → Vercel env `VITE_SENTRY_DSN`.
- Triage order: **new issues** → **regressed** → ** spikes in affected users**.
- Every request carries `X-Request-ID` (response header + log line) — paste it into Sentry "Tags" to correlate a user report with logs.
- `send_default_pii=False` — no emails/IPs attached; identify users manually via `user_id` tag if needed.

## Contacts

- Repo owner: palyatish81550 (GitHub: palyatish-1506)
- Render dashboard: https://dashboard.render.com
- Vercel dashboard: https://vercel.com
- Support: https://devin.ai/support (agent), Render/Vercel status pages for outages.

## Rate limits cheat-sheet

| Endpoint | Limit |
|---|---|
| login | 5/min/IP (100/min local dev) |
| register | 10/hour/IP |
| submit | 30/min/user |

If users report 429s during an event: it's the limiter working — wait a minute or raise `THROTTLE_*` envs temporarily.
