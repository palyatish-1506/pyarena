# 0001 — PostgreSQL driver: psycopg2-binary instead of psycopg3

## Context
The spec calls for PostgreSQL. Django supports two drivers: `psycopg` v3
(`psycopg[binary]`) and `psycopg2`. I initially pinned `psycopg[binary]>=3.2`.

## Problem discovered
On this Windows machine, importing psycopg3 fails:

```
ImportError: DLL load failed while importing _psycopg:
An Application Control policy has blocked this file.
```

An Application Control / WDAC-style policy blocks the unsigned C extension.
This would break local `manage.py` commands, migrations, and pytest for the
user — while CI (Linux) and Render (Linux) would work fine, creating a
"works in CI, broken locally" trap.

## Decision
Use `psycopg2-binary>=2.9` in `backend/requirements.txt`. Django's
`django.db.backends.postgresql` backend supports both drivers and prefers
psycopg3 when present; with only psycopg2 installed it uses psycopg2.

## Alternatives considered
- **Keep psycopg3 + ask user to relax the policy** — possible, but it's the
  user's machine security policy; not worth fighting for a driver choice.
- **SQLite for local dev** — rejected: spec mandates PostgreSQL, and dialect
  differences (e.g. `SELECT 1` health check is fine, but JSON fields, indexes,
  constraints differ) would hide real bugs.
- **psycopg3 pure-Python mode** — psycopg3 requires the C extension for
  practical use; there is no maintained pure-Python fallback.

## Consequences
- Local dev, CI, and Render all use psycopg2 — consistent everywhere.
- psycopg2 is mature and stable; performance is fine at our scale (~450 users).
- If the machine policy is later relaxed, we can switch back to psycopg3 by
  changing one line in requirements.txt (Django auto-detects).
