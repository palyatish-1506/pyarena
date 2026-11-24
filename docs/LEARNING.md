# LEARNING.md — PyArena engineering journal

Read this first. Each entry explains a concept we use, why PyArena needs it,
where it lives, a tiny example, and a "try it yourself" exercise.

---

## 0. The big picture: what each tool does

| Tool | Job in PyArena |
|---|---|
| **Django** | The backend web framework. Gives us models (database tables as Python classes), migrations (versioned schema changes), an admin panel, auth, and URL routing. |
| **DRF (Django REST Framework)** | Turns Django into a JSON API. Serializers convert model data ↔ JSON; views handle requests; permissions/authentication plug in. |
| **drf-spectacular** | Auto-generates OpenAPI docs for our API at `/api/docs/` — a live, clickable API explorer. |
| **SimpleJWT** | Issues JSON Web Tokens for login. The frontend stores an access token and sends it as `Authorization: Bearer <token>` on each request. |
| **PostgreSQL** | Our production database — real, concurrent, reliable. Locally it runs in Docker (`docker-compose.yml`); in prod it's a managed DB (Neon/Render). |
| **React** | Builds the UI as components — `HomePage`, `Layout`, etc. re-render when data changes. |
| **Vite** | Dev server + bundler for the frontend. Instant hot-reload, and `vite build` produces optimized static files for Vercel. |
| **TypeScript** | JS + static types — catches bugs before runtime (`npx tsc --noEmit` must pass in CI). |
| **Tailwind CSS** | Utility-first styling: `className="text-primary-600 font-bold"` instead of separate CSS files. v4 runs as a Vite plugin. |
| **TanStack Query** | Fetches/caches server data in React. Our `useQuery({ queryKey: ["health"], queryFn: api.health })` handles loading/error/success states for us. |
| **Axios** | HTTP client — spec mandates a single API layer in `frontend/src/api/`. Gives us interceptors (auth tokens later), timeouts, and consistent error handling vs raw `fetch`. |
| **pytest / Vitest** | Backend / frontend test runners. |
| **ruff / ESLint / Prettier** | Linting (catch bugs/style) and formatting. CI fails the PR if these fail. |
| **GitHub Actions (CI)** | Runs all checks automatically on every PR — nothing merges broken. |
| **Docker / docker-compose** | Packages Postgres so `docker compose up -d` gives everyone the same database locally. |
| **Render / Vercel** | Hosting: Render runs the Django API (Docker), Vercel serves the built React app. |

---

## 1. How a request travels: browser → database → browser

Using our health check as the example:

1. `HomePage` calls `useQuery({ queryKey: ["health"], queryFn: api.health })`.
2. `api.health()` (`frontend/src/api/index.ts`) calls `apiClient.get(...)` —
   an **Axios** instance from `src/api/client.ts`. `baseURL` is empty in dev,
   so the request goes to `/api/v1/health/` on the Vite origin.
   - In dev, Vite's proxy (`vite.config.ts`) forwards `/api/*` to `localhost:8000`,
     so the browser never deals with CORS locally.
   - In prod, `VITE_API_BASE_URL` points straight at the Render URL.
3. Django's URL router (`backend/config/urls.py`) matches `api/v1/health/` →
   the `health` view in `backend/config/views.py`.
4. The view opens a DB cursor and runs `SELECT 1` — proving Postgres is reachable.
5. It returns `JsonResponse({"status": "ok", "db": "ok"})`.
6. TanStack Query caches the result; React re-renders "Backend connected ✓".

**Try it yourself:** open `http://localhost:8000/api/docs/` and click
`GET /api/v1/health/` → "Try it out" → "Execute". You're calling the API without
the frontend — great for debugging.

---

## 2. Project structure

```
PyArena/
├── backend/            Django project (config = project, apps = features)
│   ├── config/         settings, urls, wsgi — the "glue"
│   ├── accounts/       custom User model, auth (Milestone 1)
│   ├── questions/      quiz questions      (empty for now)
│   ├── submissions/    quiz answers        (empty for now)
│   ├── leaderboard/    rankings            (empty for now)
│   ├── gamification/   XP, streaks         (empty for now)
│   └── community/      discussions         (empty for now)
├── frontend/           React + Vite + TS + Tailwind app
├── docs/               this file, spec, changelog, ADRs
├── docker-compose.yml  local Postgres
└── .github/workflows/  CI
```

**Why apps?** Django splits a project into "apps" — self-contained feature
modules. `accounts` owns users; `questions` will own quizzes. Each app has
`models.py` (database tables), `views.py` (API endpoints), `serializers.py`
(JSON conversion), `migrations/` (schema history), `tests/`.

**Try it yourself:** `cd backend && python manage.py startapp todo` creates a
new empty app — then add `"todo"` to `INSTALLED_APPS` in
`config/settings/base.py`.

---

## 3. Django settings split (base / dev / prod)

- `config/settings/base.py` — everything shared. Reads config from environment
  variables via **django-environ** (`env("SECRET_KEY")`, `env.db("DATABASE_URL")`).
- `dev.py` — `DEBUG = True`, used by `manage.py runserver` and pytest.
- `prod.py` — `DEBUG = False`, HTTPS cookies, HSTS, and it *refuses to boot*
  without a real `SECRET_KEY`.
- `TIME_ZONE = "Asia/Kolkata"` (spec: IST display) with `USE_TZ = True`, so the
  DB always stores UTC and Django converts for display.

**Why?** You never want `DEBUG=True` in production (it leaks internals on
errors). And secrets must never live in code — only in env vars.

**Where:** `backend/config/settings/{base,dev,prod}.py`, `.env.example` at root.

**Try it yourself:** run `python manage.py shell` then
`from django.conf import settings; print(settings.DATABASES)` — see where the
DB config came from.

---

## 4. The custom User model

`backend/accounts/models.py` defines `User` extending Django's `AbstractUser`
with `email` as the login field (`USERNAME_FIELD = "email"`), plus the spec's
profile fields: `full_name`, `roll_no` (unique), `branch`, `year`, `division`,
`role` (student/senior/admin), `senior_approved`, and the gamification fields
(`xp`, `level`, streaks, `avatar_seed`). It was created **before the first
migration** — Django's golden rule, because changing `AUTH_USER_MODEL` later
is painful.

**Why?** PyArena needs roles (students vs mentors vs admins) and email login.

**Try it yourself:**
```bash
python manage.py shell
>>> from accounts.models import User
>>> u = User.objects.create_user("me@test.com", "pw", display_name="Me")
```

---

## 5. Migrations

`accounts/migrations/0001_initial.py` is a generated, versioned record of "create
the users table". `manage.py migrate` applies pending migrations to the DB.
Think `git` for your schema.

**Try it yourself:** after adding a field to `User`, run
`python manage.py makemigrations && python manage.py migrate` — watch the new
file appear.

---

## 6. DRF, serializers & the health endpoint

Our health view is a plain Django view returning `JsonResponse` — fine for a
ping. Real endpoints will use DRF: a **serializer** converts a model instance
into JSON and validates incoming JSON back into model data; a **viewset**
wires list/create/retrieve/update/delete to URLs automatically.

**Where:** `backend/config/urls.py` mounts `api/v1/`; DRF config lives in
`REST_FRAMEWORK` in `settings/base.py`; SimpleJWT will handle `/api/v1/auth/`
in Milestone 1.

**Try it yourself:** browse `/api/docs/` — every endpoint we add appears there
automatically.

---

## 7. JWT authentication (coming in Milestone 1)

SimpleJWT issues two tokens: a short-lived **access token** (sent on every
request) and a longer **refresh token** (used to get a new access token without
re-login). The frontend will store them and attach
`Authorization: Bearer <access>` via the central API client.

**Try it yourself (later):** `POST /api/v1/auth/token/` with email+password →
get tokens → call a protected endpoint with the Bearer header.

---

## 8. docker-compose

`docker-compose.yml` defines a `db` service: `postgres:16-alpine` with a named
volume (data survives restarts) and a healthcheck. `docker compose up -d`
starts it in the background; credentials match `.env.example`.

**Why?** Everyone gets an identical Postgres without installing it; prod uses
the same engine so "works on my machine" actually means something.

**Try it yourself:** `docker compose up -d`, then
`docker compose exec db psql -U pyarena -d pyarena` → `\dt` lists tables.

---

## 9. CI (GitHub Actions)

`.github/workflows/ci.yml` runs on every PR: **backend** job installs deps,
runs `ruff check` and `pytest` against a real Postgres *service container*;
**frontend** job runs `npm ci`, `eslint`, `tsc --noEmit`, `vitest`. Any failure
blocks merge — the "quality bar".

**Try it yourself:** intentionally break a lint rule, push, watch CI go red,
then fix it.

---

## 10. Environment variables & secrets

`.env` (git-ignored) holds local secrets; `.env.example` documents every var.
In prod, Render/Vercel inject env vars — **never** commit real values.
`frontend/.env` uses `VITE_` prefix (only those reach the browser bundle —
never put secrets there).

**Try it yourself:** `SECRET_KEY=foo python manage.py check` vs leaving it
default — prod settings refuse to boot without it.

---

## 11. Deployment: Render + Vercel

- **Render** (`render.yaml`): builds `backend/Dockerfile` (pip install →
  collectstatic → `gunicorn config.wsgi`), provisions a managed Postgres,
  injects `DATABASE_URL`/`SECRET_KEY`, health-checks `/api/v1/health/`.
- **Vercel** (`frontend/vercel.json`): runs `npm run build`, serves `dist/` as
  static files, SPA rewrite sends all routes to `index.html`.
- **whitenoise** serves Django's static files (admin CSS/JS) without nginx.

**Try it yourself:** after deploy, `curl https://<api>/api/v1/health/`.

---

## 12. ADRs — why psycopg2 instead of psycopg3

See `docs/decisions/0001-psycopg2-driver.md`. Short version: this Windows
machine's Application Control policy blocks psycopg3's C extension DLL;
psycopg2-binary works everywhere we need it. Revisit if the policy changes.
