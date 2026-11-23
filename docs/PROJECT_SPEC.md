# PROJECT_SPEC.md — PyArena (source of truth)

## 1. Mission
PyArena is a web platform for ~450 junior college students learning Python.
Seniors (~20) publish questions (replacing WhatsApp polls); juniors answer,
get instant explanations, earn points, levels, badges and streaks, and compete
on fair, resetting leaderboards. Mobile-first: most users are on mid-range
Android phones over mobile data.

The owner is a learning developer. Every piece of backend work must also teach:
explain what you built and why in docs/LEARNING.md.

## 2. Users & roles
- STUDENT: register, answer questions, view progress, leaderboards, comment.
- SENIOR: everything a student can + create/edit/schedule questions, view
  question stats, answer doubts. Must be approved by an admin.
- ADMIN: everything + approve seniors, manage users/divisions, moderation,
  CSV export. Uses Django admin + in-app admin screens.

## 3. FINAL tech stack (do not change without asking the owner)
Backend
- Python 3.12, Django 5.x, Django REST Framework
- djangorestframework-simplejwt (JWT auth)
- PostgreSQL 16 (local via Docker; production on Neon or Supabase)
- django-cors-headers, django-environ, drf-spectacular (OpenAPI docs)
- django-ratelimit (or DRF throttling) for login/submit
- pytest + pytest-django + factory_boy for tests
- ruff (lint + format)
- Gunicorn for production
- Later milestones only: Django Channels + Redis (live quiz), Sentry SDK
Frontend
- React 18 + Vite + TypeScript (strict mode)
- Tailwind CSS, React Router, TanStack Query (server state), Zod (validation)
- Axios API client in src/api/ (single place for all backend calls)
- Vitest + React Testing Library; Playwright for end-to-end
- ESLint + Prettier
- Pyodide (in a Web Worker) for running Python in the browser (later milestone)
Infra
- Monorepo on GitHub: /backend, /frontend, /docs
- docker-compose for local Postgres (and Redis later)
- GitHub Actions CI: lint + tests for backend and frontend on every PR
- Deploy: backend on Render (or Railway), frontend on Vercel
- Secrets ONLY via environment variables. Commit .env.example, never .env.

## 4. Architecture rules
- Modular monolith. Django apps: accounts, questions, submissions,
  leaderboard, gamification, community, livequiz (later), analytics (later).
- Business logic lives in services.py per app (not in views or serializers).
- Views thin; serializers validate; services do the work; models store.
- All API routes under /api/v1/. Auto-generated docs at /api/docs/.
- Never send correct answers to the client before the user submits.
- All permission checks happen on the server.
- Use database constraints for integrity (e.g. UNIQUE(user, question)).
- Time zone: Asia/Kolkata for display; store UTC.

## 5. Data model (core)
User(custom, extends AbstractUser): email (unique, login), full_name,
  roll_no (unique), branch, year, division, role [student|senior|admin],
  senior_approved (bool), xp, level, current_streak, longest_streak,
  streak_freezes (int), last_active_date, avatar_seed, created_at
Topic: name, slug, order, description
Question: author→User, topic→Topic, type [mcq_single|mcq_multi|output],
  title, body_markdown, code_snippet, difficulty [easy|medium|hard],
  explanation_markdown, base_points, release_at, close_at, status
  [draft|scheduled|published|archived], created_at, updated_at
Option: question→Question, text, is_correct, order
Submission: user→User, question→Question, selected_option_ids (array/json),
  is_correct, points_awarded, time_taken_ms, is_late (practice only),
  submitted_at. UNIQUE(user, question).
Badge: code (unique), name, description, icon
UserBadge: user, badge, earned_at. UNIQUE(user, badge)
Season: name, start_date, end_date, is_active
Comment: question, user, parent (nullable), body, upvotes, created_at,
  is_hidden
(Later) TestCase, CodeProblem, LiveQuiz, LiveQuizParticipant

## 6. Scoring & gamification rules
- Correct answer: base_points (easy 10, medium 20, hard 30)
- Speed bonus: up to +50% of base if answered in the first 10% of the open
  window, decaying linearly to 0 at 50% of the window.
- Wrong answer: 0 points. No negative marking.
- Late answer (after close_at): 0 points, counts for practice and streak.
- Option order is shuffled per user (deterministic seed = user_id+question_id).
- Streak: +1 for each calendar day (IST) with ≥1 submission. One freeze earned
  per 7-day streak (max 2), consumed automatically on a missed day.
- Levels by XP and topic mastery:
  L1 Print Padawan (0), L2 Variable Voyager (100), L3 Loop Learner (300),
  L4 Function Master (700), L5 Data Wizard (1500), L6 Pythonista (3000).
  A level also requires ≥60% accuracy on its matching topic.
- Badges (initial): first_answer, streak_7, streak_30, first_hard_correct,
  perfect_week, night_owl (answer between 23:00–04:00 IST), helper_10
  (10 upvoted comments), top10_weekly.

## 7. Leaderboards (all must exist)
- Weekly overall (resets Monday 00:00 IST)
- Weekly per division
- Division vs division (average points per active member)
- Most improved (this week vs last week)
- Beginner league (users below Level 3)
- Season overall
- Always show the current user's own rank and the gap to the next rank,
  even if outside the top 50.
- Cache leaderboard responses for 60 seconds.

## 8. Design direction (Devin: follow this, do not invent a different style)
- Mobile-first. Test at 375px and 1440px widths.
- Clean, friendly, slightly playful. Light theme default + dark mode.
- Palette: primary #3776AB (Python blue), accent #FFD43B (Python yellow),
  success #16A34A, error #DC2626, neutral slate greys. WCAG AA contrast.
- Font: Inter for UI, JetBrains Mono for code.
- Code blocks with syntax highlighting (Shiki or Prism).
- Key screens: Landing, Register/Login, Home (today's challenge, streak,
  level progress), Question view, Result + explanation (with confetti on
  correct), Leaderboards (tabs), Profile, Topic progress, Senior dashboard
  (create/schedule/stats), Admin screens.
- Pages must load fast on 4G: keep the JS bundle small and lazy-load routes.

## 9. Quality bar (definition of done for every PR)
- Lint passes (ruff, eslint), type-check passes (tsc --noEmit)
- Backend tests pass; coverage of services ≥ 85%
- Frontend tests pass; at least one Playwright happy path per feature
- New endpoints documented in OpenAPI
- docs/LEARNING.md updated with a beginner-friendly explanation
- docs/CHANGELOG.md updated
- Screenshots at 375px and 1440px attached to the PR for UI changes
- No secrets in code; .env.example updated if new variables were added

## 10. Non-goals for v1
No native mobile app, no payments, no AI tutor, no chat/DMs, no other
colleges, no microservices, no Kubernetes.
