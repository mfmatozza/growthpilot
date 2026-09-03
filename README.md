# GrowthPilot

Self-hosted SEO + GEO (generative-engine-optimization) automation platform. Single site to start,
architected for multi-site later (see `docs/DECISIONS.md`).

Modules: (1) keyword & topic research, (2) article generation, (3) technical SEO audit, (4) AI-search
visibility tracking, (5) Reddit/community monitoring. Status of each — what's built vs. stubbed — is in
[Build status](#build-status) below.

## Live

- Frontend: https://frontend-production-e032.up.railway.app
- Backend: https://backend-production-24d1e.up.railway.app (docs at `/docs`)

These are Railway's auto-generated domains (no custom domain attached). Login at `/login` — single admin
account, see docs/DECISIONS.md #16 for how to change the password.

## Stack

- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.0 + Alembic, PostgreSQL
- Frontend: React + TypeScript + Tailwind, Vite, React Router
- LLM: OpenAI by default, Anthropic as a one-line config swap (docs/DECISIONS.md #15)
- Scheduling: APScheduler, running in-process — weekly technical audits and GEO checks fire on their own
  once deployed, no external cron (`app/scheduler/scheduled_jobs.py`, decisions doc #20)

## Quickstart (Docker Compose)

```bash
cp .env.example .env   # fill in at least OPENAI_API_KEY, ADMIN_EMAIL, ADMIN_PASSWORD
docker compose up --build
```

- Frontend: http://localhost:3100
- Backend API: http://localhost:8000 (docs at /docs)
- Postgres: localhost:5434 (not 5432 — see decisions doc #12)

The `backend` container doesn't run migrations automatically. First time up:

```bash
docker compose exec backend alembic upgrade head
```

## Local dev without Docker

Backend:

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d db          # just the DB
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev                      # always :3100, see vite.config.ts
```

## Tests

```bash
cd backend
source .venv/bin/activate
pytest
```

All external services (every LLM provider, DataForSEO, PageSpeed Insights, the crawler's HTTP fetcher) are
behind interfaces in `app/services/*` with fake/mock implementations in the same package, so the test suite
runs with no network access and no API keys.

## Deployment (Railway)

Live project: both `backend` and `frontend` run as separate services in one Railway project, alongside a
Postgres plugin, per docs/DECISIONS.md #14. Infrastructure is defined as code in `.railway/railway.ts`
(Railway's IaC tool — `npm install` at the repo root pulls in the `railway` SDK it imports).

To reproduce or modify:

```bash
npm install -g @railway/cli
railway login
railway link            # link this directory to the growthpilot project
railway config plan     # preview drift between railway.ts and the live project
railway config apply    # apply railway.ts
```

Each service auto-deploys on push to `main` (GitHub-connected, root directory set to `backend/` and
`frontend/` respectively via `railway.ts`). A few things that don't live in `railway.ts` and were set
by hand once — reproduce with `railway variable set` / `railway domain` if rebuilding from scratch:

- `backend`'s `DATABASE_URL` references the Postgres plugin (`${{Postgres.DATABASE_URL}}`); the app
  normalizes its `postgres(ql)://` scheme to `postgresql+psycopg://` itself (`app/core/config.py`).
- `backend`'s `CORS_ALLOWED_ORIGINS` must include the frontend's public domain.
- `frontend`'s `VITE_API_BASE_URL` must be the backend's public domain — it's a Docker **build arg**
  (Vite inlines it at build time), so changing it requires `railway redeploy --from-source`, not just a
  restart — see `frontend/Dockerfile` and docs/DECISIONS.md #14.
- API keys (see Config below) are set on `backend` per the table there — `OPENAI_API_KEY`, `ADMIN_EMAIL`/
  `ADMIN_PASSWORD` and the LLM/GEO/audit keys are live; DataForSEO, SerpAPI, image, and Reddit keys are not.
- A freshly auto-generated Railway domain occasionally never wires up to its service (returns the
  platform's own 404 "Application not found" indefinitely); deleting and recreating it with an explicit
  `--port` fixed it every time this happened during setup.

No secrets live in `railway.ts` — it references the Postgres plugin's variable rather than inlining it.

## Config

Every external API key is optional at boot — the app starts fine with none of them set. Each pipeline
raises a clear 4xx error (not a crash) the first time it's actually invoked without its required key.
See `.env.example` for the full list and which module needs what.

Required to use each module:

| Module | Needs |
|---|---|
| 1. Keyword research | `OPENAI_API_KEY` (site profile + candidates); `DATAFORSEO_LOGIN`/`DATAFORSEO_PASSWORD` optional (adds volume/difficulty — candidates still generate without it) |
| 2. Article generation | `OPENAI_API_KEY`; `SERPAPI_KEY` optional (competitor SERP research — works without it, from the model's own knowledge instead; see docs/DECISIONS.md #25). No image generation — images were dropped per explicit request |
| 3. Technical audit | `OPENAI_API_KEY` (summarization); `GOOGLE_PAGESPEED_API_KEY` optional (PageSpeed Insights works keyless at low volume) |
| 4. GEO tracker | at least one of `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_GEMINI_API_KEY` / `PERPLEXITY_API_KEY` — skips whichever aren't set rather than failing |
| 5. Reddit monitor | hidden from the UI — Reddit closed self-service API registration in late 2025, no path to credentials right now (docs/DECISIONS.md #29) |

## Build status

Per the project brief's build order:

1. ✅ Scaffolding — FastAPI backend, Postgres schema + Alembic migrations, Docker Compose, React shell with routing
2. ✅ Module 1 (keyword research) — crawl → site profile → candidate keywords → DataForSEO enrichment → opportunity score → review UI (Keywords tab)
3. ✅ Module 2 (article generation) — outline → section-by-section draft → internal linking pass, Markdown
   output, no images, explicit anti-AI-tell instructions (no em dashes, no stock phrasing — verified against
   the real API). Comparison-mode template for multi-option articles. Wired into weekly automation as
   auto-draft only (never auto-publish — see docs/DECISIONS.md #27)
4. ✅ Module 4 (GEO tracker) — queries every configured provider (ChatGPT/Claude/Gemini/Perplexity) against your top approved keywords, analyzes mentions/competitors, visibility chart + "not yet mentioned" queue
5. ✅ Module 3 (technical audit) — crawl checks (broken links, missing titles/meta/alt text, duplicate titles) + PageSpeed Insights, summarized and severity-ranked by an LLM
6. 🟡 Module 5 (Reddit monitor) — backend fully built (searches configured subreddits, drafts never-auto-
   posted replies), but **hidden from the frontend entirely**: Reddit closed self-service API registration
   in late 2025, so there's currently no path to real credentials (see docs/DECISIONS.md #29). All the code
   is still there, ready to re-wire (one route + one nav item) the moment access exists.
7. ✅ Scheduling/automation layer — Modules 3 and 4 run automatically every Monday, in-process (`app/scheduler/scheduled_jobs.py`); both also have manual "run now" buttons
8. ⬜ Dashboard polish pass

## Architecture decisions

Every judgment call made without asking is logged in [`docs/DECISIONS.md`](docs/DECISIONS.md), including
why. Worth reading before extending this — in particular #4 (the Claude model id in the brief isn't real,
it's a config value now) and #9 (the FastAPI backend should not be deployed as Vercel serverless functions).
