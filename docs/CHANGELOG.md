# Changelog

## [0.1.0] — Milestone 0: Foundation & walking skeleton — DEPLOYED

Live: API https://pyarena-api.onrender.com · Web https://pyarena-indol.vercel.app

### Added
- Monorepo layout: `backend/` (Django `config` + 6 apps), `frontend/` (Vite +
  React + TS + Tailwind + TanStack Query), `docs/`.
- Backend: base/dev/prod settings via django-environ, custom `accounts.User`
  (email login, roles), DRF + drf-spectacular (`/api/docs/`), SimpleJWT config,
  `GET /api/v1/health/`, env-driven CORS, whitenoise, ruff, pytest.
- Frontend: app layout with nav, Tailwind theme, Home page with live backend
  health check through a central API client, ESLint + Prettier, Vitest.
- Infra: `docker-compose.yml` (Postgres 16), `backend/Dockerfile`, `render.yaml`,
  `frontend/vercel.json`, GitHub Actions CI (ruff+pytest on PG service;
  eslint+tsc+vitest).
- Docs: LEARNING.md, decisions/0001 (psycopg2 driver), README.
- Playwright e2e (home page happy paths) + `npm run screenshots` for the
  375px/1440px PR screenshots in docs/screenshots/.
- Deploy: backend Dockerfile runs `migrate` on boot; render.yaml CORS/CSRF
  point at the Vercel origin.

### Notes
- Local Postgres access pending credentials; verified with SQLite
  `DATABASE_URL` override. CI exercises real Postgres 16.
- Aligned to spec: User model has full_name/roll_no/branch/year/division/
  role(student|senior|admin)/senior_approved + gamification fields; roles are
  student/senior/admin (not mentor); palette is Python blue #3776AB +
  #FFD43B; API client is Axios in `frontend/src/api/`; TIME_ZONE=Asia/Kolkata
  with UTC storage; DRF throttling configured for login/submit.
