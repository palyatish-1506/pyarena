# PyArena

A Python learning and quiz platform for ~450 college students.
Django 5 + DRF + PostgreSQL backend, React + Vite + TypeScript + Tailwind
frontend, deployed on Render + Vercel.

## Run locally in 5 minutes

Prereqs: Python 3.12+, Node 20+, Docker Desktop (for Postgres).

### 1. Database

```bash
docker compose up -d          # starts Postgres 16 on :5432
docker compose ps             # wait for "healthy"
```

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp ../.env.example ../.env    # already have one? skip
python manage.py migrate
python manage.py runserver    # http://localhost:8000
```

API docs: http://localhost:8000/api/docs/
Health:   http://localhost:8000/api/v1/health/

> No Docker? Any local Postgres works — point `DATABASE_URL` in `.env` at it.
> Emergency fallback: `DATABASE_URL=sqlite:///db.sqlite3` works for dev/tests.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

The Home page should show **"Backend connected ✓"** — Vite proxies `/api`
to Django automatically.

### 4. Checks (what CI runs)

```bash
cd backend  && ruff check . && pytest
cd frontend && npm run lint && npx tsc --noEmit && npm test
```

## Repo map

| Path | What |
|---|---|
| `backend/config/` | Django project: settings (base/dev/prod), URLs, WSGI |
| `backend/accounts/` | Custom `User` model (email login, roles) |
| `backend/{questions,submissions,leaderboard,gamification,community}/` | Feature apps (filled in later milestones) |
| `frontend/src/` | React app: `lib/api.ts` (API client), `pages/`, `components/` |
| `docs/` | `LEARNING.md` (start here!), `PROJECT_SPEC.md`, `CHANGELOG.md`, `decisions/` |
| `.github/workflows/ci.yml` | CI: lint + tests on every PR |
| `render.yaml`, `backend/Dockerfile`, `frontend/vercel.json` | Deployment config |

## Deployment

- **Backend → Render:** blueprint in `render.yaml` (Docker). Set env vars per
  `.env.example`; `SECRET_KEY` auto-generates.
- **Frontend → Vercel:** import repo, root directory `frontend`, framework
  auto-detected; set `VITE_API_BASE_URL` to the Render URL.

See `docs/LEARNING.md` §11 for details.
