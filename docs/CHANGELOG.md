# Changelog

## [Unreleased] — Milestone 7: Kahoot-style live quiz

### Added
- livequiz app: LiveQuiz (6-digit code, lobby→live→reveal→finished),
  LiveQuizParticipant, LiveQuizAnswer (UNIQUE per question, first wins)
- Django Channels QuizConsumer: JWT auth via ?token=, host controls
  (start/next/reveal/end), server-scheduled auto-reveal + manual reveal,
  scoring at reveal (correct=exact set, faster=more points), live
  leaderboard broadcasts
- REST: POST /live/create (senior), GET /live/<code>/, GET /live/mine/
- ASGI ProtocolTypeRouter (http+websocket); CHANNEL_LAYERS Redis when
  REDIS_URL set else InMemory; deps: channels, channels-redis, daphne,
  uvicorn
- Frontend /live/:code player+host screen (join, answer, reveal, podium)
- C1: 3-client full-quiz pytest passes


## [Unreleased] — Milestone 5: Badges, levels UI & doubt comments

### Added
- Badge engine (gamification/services.py): 8 badges per spec §6 —
  first_answer, streak_7/30, first_hard_correct, perfect_week, night_owl,
  helper_10, top10_weekly; idempotent get_or_create awarding evaluated
  after every submission/comment.
- community app: threaded (1-level) comments under questions, gated 403
  until the user submits; upvotes, senior "accepted answer", report
  button, admin is_hidden, COMMENT_BAD_WORDS profanity filter.
- Frontend: comments section on question page (post-submit), badge
  gallery on profile, level-up modal on submit, badges in /me/badges.
- Tests: badge rules + level thresholds + comment gating/flow/profanity;
  e2e extended: submit -> first_answer badge on profile.


## [Unreleased] — Milestone 3: Answering, scoring & explanations

### Added
- Backend: `Submission` model (UNIQUE(user,question)); `submit_answer`
  service — transaction + select_for_update, exact-set correctness
  (multi partial = wrong), speed bonus (first 10% of window, +50% max),
  late=practice (0 pts, streak counts), IST streaks with freezes,
  XP/level/badges; `POST /api/v1/questions/{id}/submit` (30/min),
  `GET /api/v1/me/history` (paginated), `GET /api/v1/me/topics`.
- Frontend: answer flow with live timer, result panel (confetti on
  correct, explanation markdown, practice-mode label, XP/level/streak),
  `/history` page, topic progress bars on profile, XP/streak chips on home.
- Fix: single-flight token refresh (concurrent refresh calls killed sessions).
- Tests: 13 submission pytest cases incl. speed-bonus edges, late,
  duplicate 409, multi partial, IST streak + freeze, threaded
  concurrency (exactly 1 of 2 parallel submits wins); Playwright
  answer→explanation→XP e2e.

## [Unreleased] — Milestone 2: Question authoring

### Added
- Backend: `Topic`/`Question`/`Option` models + indexes `(status,release_at)`,
  `(topic,difficulty)`; `services.py` (validation, create/duplicate,
  query-time visibility, deterministic per-user shuffle);
  `StudentQuestionSerializer` that structurally cannot leak answers;
  `IsSeniorOrAdmin` permission; endpoints `/api/v1/questions/{today,topics,{id}}`
  and `/api/v1/questions/senior/questions` CRUD + duplicate + preview.
- `seed_topics` (13 topics, 34 questions) and `seed_demo` (senior+student).
- Frontend: `/senior` dashboard (builder with markdown+code+options editor,
  IST schedule picker, live student preview, status-filtered list,
  duplicate), Today's Challenge on Home, `/questions/:id` detail with
  option selection, `CodeBlock` (Prism Python highlighting), `Markdown`
  renderer, `lib/time.ts` IST↔UTC helpers, `SeniorOnly` route guard.
- Tests: 15 pytest (leak-proof, scheduling, validation, shuffle,
  permissions, duplicate, preview) + Playwright senior→schedule→student e2e.
- C4 timing: senior dashboard → saved draft in **0.4s** (target <60s).

## [Unreleased] — Milestone 1: Authentication

### Added
- Backend: `accounts/services.py` (register_user), `serializers.py`,
  `authentication.py` (CookieJWTAuthentication), `cookies.py`, `views.py`,
  `urls.py` — endpoints `POST /api/v1/auth/register|login|refresh|logout`,
  `GET /api/v1/auth/me/`. Tokens delivered as httpOnly cookies (ADR-0002).
- Cookie flags env-configurable; prod forces `SameSite=None; Secure`.
- DRF default auth switched to cookie JWT; login endpoint throttled
  (`THROTTLE_LOGIN_RATE`).
- Frontend: Axios `withCredentials` + silent-refresh interceptor, `AuthProvider`
  context, Zod schemas, `/login` + `/register` pages, `ProtectedRoute`,
  `/profile` page, auth-aware nav.
- Tests: 7 backend auth tests, 3 vitest auth tests, Playwright register→
  profile→logout e2e.
- Docs: ADR-0002, LEARNING.md §7/§13/§14.

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
