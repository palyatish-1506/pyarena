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

## 7. JWT authentication — cookie edition

SimpleJWT issues two tokens: a short-lived **access token** and a longer
**refresh token**. We chose **httpOnly cookies** (ADR-0002) over
localStorage + Bearer headers: the browser attaches cookies automatically,
JavaScript can never read them, and XSS can't steal them.

How it works in our code:
- `accounts/views.py` — login/register validate credentials via SimpleJWT
  serializers, then `accounts/cookies.py` sets `access_token` /
  `refresh_token` as httpOnly cookies.
- `accounts/authentication.py` — `CookieJWTAuthentication` teaches DRF to
  read the JWT from the cookie (stock JWTAuthentication only reads headers).
- `frontend/src/api/client.ts` — Axios uses `withCredentials: true`; a
  response interceptor silently calls `/auth/refresh/` on 401 and retries.
- `frontend/src/auth/AuthContext.tsx` — on app load it calls `/auth/me/`;
  the cookie decides whether you're logged in. No tokens in JS memory.

Prod wrinkle: vercel.app → onrender.com is **cross-site**, so cookies need
`SameSite=None; Secure` (set in `settings/prod.py`); dev uses `SameSite=Lax`.

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

## 12. ADRs

- `docs/decisions/0001-psycopg2-driver.md` — why psycopg2, not psycopg3.
- `docs/decisions/0002-cookie-based-jwt.md` — why httpOnly cookies over
  localStorage for JWT delivery.

## 13. Zod + form validation (frontend)

`frontend/src/auth/schemas.ts` defines Zod schemas — a TypeScript-first way
to declare "what a valid form looks like" once, get both runtime validation
and inferred types (`z.infer`). The auth pages call `schema.safeParse(form)`
on submit; field errors map straight onto inputs. Backend still re-validates
(DRF serializers) — client validation is UX, server validation is security.

**Try it yourself:** add a `confirm` field rule to `registerSchema` and watch
the type error guide you.

## 15. ORM relationships & the questions app (Milestone 2)

Three models in `backend/questions/models.py`:
- `Topic` — standalone (PROTECT: can't delete a topic that has questions).
- `Question` — FK to `author` (User) and `topic`; `type`/`difficulty`/`status`
  are `TextChoices` (Python enums stored as short strings).
- `Option` — FK to Question with `related_name="options"`, so
  `question.options.all()` just works. `UniqueConstraint(question, order)`
  stops two options sharing a position.

**Indexes matter at scale:** `Index(fields=["status","release_at"])` makes
"what's live right now?" an index scan, not a table scan; `(topic,
difficulty)` speeds filtered browsing. Migrations (`questions/migrations/`)
are generated by `makemigrate` — never edit them by hand.

**Try it yourself:** `python manage.py shell` →
`Question.objects.filter(status="published").count()`

## 16. Serializers that hide fields (the C1 trick)

`StudentQuestionSerializer` simply **doesn't declare** `is_correct` or
`explanation_markdown`. DRF only outputs declared fields, so answer data
*cannot* leak — it's not "filtered out", it doesn't exist in the shape.
The senior serializer is a separate class with full fields. Two shapes,
two audiences, zero shared leakage.

**Why answers stay server-side:** if correctness ever reached the browser
before submit, anyone could open devtools and cheat. Submissions (M3)
will POST answers; the server computes correctness.

## 17. Query-time visibility (no cron needed)

`services.visible_to_students()` returns `status IN (published, scheduled)
AND release_at <= now`. A "scheduled" question whose release time passes
becomes visible automatically — the status is a *label*, visibility is a
*query*. No Celery/cron job required for M2.

## 18. Deterministic per-user shuffle

`random.Random(user_id + question_id).shuffle(options)` — same user sees
the same order every time (no flicker on refresh), different users get
different orders. Python's `random` is seeded, so it's reproducible —
that's the point (spec §6).

## 19. Timezones: IST display, UTC storage

Django `USE_TZ=True` stores UTC always. `TIME_ZONE="Asia/Kolkata"` only
affects display. Frontend `src/lib/time.ts`: seniors type IST wall-clock
into `datetime-local`; `istLocalToUtcIso()` appends `+05:30` and converts
to a UTC ISO string for the API.

**Try it yourself:** `python manage.py shell` →
`from django.utils import timezone; print(timezone.now())` → always UTC.

## 20. Transactions, race conditions & idempotency (Milestone 3)

`submissions/services.py::submit_answer` wraps everything in
`@transaction.atomic` and locks the user row with
`User.objects.select_for_update().get(pk=...)`. Why: two simultaneous
submits could both read `xp=0`, both add points, and lose an update —
the row lock serializes them so XP/streak math is always consistent.

**Idempotency:** `UNIQUE(user, question)` on Submission means a second
attempt raises `IntegrityError` → we translate it to HTTP 409. The
database is the final guard; the check-then-insert alone would race.

**Scoring (spec §6):** correct = base (10/20/30) + speed bonus —
+50% of base if answered in the first 10% of the open window
(release_at→close_at), decaying linearly to 0 at 50%. Wrong = 0,
no negative marking. Late (after close_at) = practice: correct but 0
points, still counts for the streak.

**Streaks in IST:** `_ist_today()` converts `timezone.now()` to a
fixed +5:30 date — streaks are IST *calendar days*, not 24h periods.
Missed days are covered by `streak_freezes` (earned per 7-day streak,
max 2) before the streak resets to 1.

**Single-flight refresh (frontend bug found by e2e):** on page load,
both AuthContext hydration and the axios 401-interceptor could call
`/auth/refresh/` at once — the second used the just-rotated token and
killed the session. `refreshAccessToken()` in `api/client.ts` dedupes
concurrent calls into one promise.

**Try it yourself:** submit the same question twice via curl — second
call returns 409.

## 14. The 401-refresh-retry interceptor

`src/api/client.ts` intercepts every failed response. On 401 (and the request
isn't already an auth endpoint), it POSTs `/auth/refresh/` — the browser
attaches the refresh cookie automatically — then retries the original
request once (`_retried` flag prevents loops). If refresh fails it fires a
`pyarena:session-expired` window event that `AuthContext` listens for to log
the user out. This is the standard "silent token refresh" pattern.

**Try it yourself:** in devtools → Application → Cookies, delete
`access_token`, reload, click something that calls the API — watch the
Network tab show a refresh call followed by a successful retry.
