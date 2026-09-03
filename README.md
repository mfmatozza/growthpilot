# GrowthPilot

Self-hosted SEO + GEO (generative-engine-optimization) automation platform. Single site to start,
architected for multi-site later (see `docs/DECISIONS.md`).

Modules: (1) keyword & topic research, (2) article generation, (3) technical SEO audit, (4) AI-search
visibility tracking, (5) Reddit/community monitoring. Status of each — what's built vs. stubbed — is in
[Build status](#build-status) below.

## Stack

- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.0 + Alembic, PostgreSQL
- Frontend: React + TypeScript + Tailwind, Vite, React Router
- LLM: Anthropic Claude API
- Scheduling: APScheduler (seam to swap in Celery + Redis later — see decisions doc #5)

## Quickstart (Docker Compose)

```bash
cp .env.example .env   # fill in at least ANTHROPIC_API_KEY to use Module 1/2
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

All external services (Claude, DataForSEO, the crawler's HTTP fetcher) are behind interfaces in
`app/services/*` with fake/mock implementations in the same package, so the test suite runs with no
network access and no API keys.

## Config

Every external API key is optional at boot — the app starts fine with none of them set. Each pipeline
raises a clear 4xx error (not a crash) the first time it's actually invoked without its required key.
See `.env.example` for the full list and which module needs what.

Required to use each module:

| Module | Needs |
|---|---|
| 1. Keyword research | `ANTHROPIC_API_KEY` (site profile + candidates); `DATAFORSEO_LOGIN`/`DATAFORSEO_PASSWORD` optional (adds volume/difficulty — candidates still generate without it) |
| 2. Article generation | `ANTHROPIC_API_KEY`; `SERPAPI_KEY` for competitor SERP research; one of `FLUX_API_KEY` / `OPENAI_API_KEY_FOR_IMAGES` / `UNSPLASH_ACCESS_KEY` for images |
| 3. Technical audit | none yet — not built |
| 4. GEO tracker | none yet — not built (`OPENAI_API_KEY`, `GOOGLE_GEMINI_API_KEY`, `PERPLEXITY_API_KEY`, plus `ANTHROPIC_API_KEY`, will be needed once it is) |
| 5. Reddit monitor | none yet — not built (`REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET` will be needed once it is) |

## Build status

Per the project brief's build order:

1. ✅ Scaffolding — FastAPI backend, Postgres schema + Alembic migrations, Docker Compose, React shell with routing
2. ✅ Module 1 (keyword research) — crawl → site profile → candidate keywords → DataForSEO enrichment → opportunity score → review UI (Keywords tab)
3. ⬜ Module 2 (article generation) — DB table + read-only API + placeholder UI only
4. ⬜ Module 4 (GEO tracker) — DB table + read-only API + placeholder UI (chart, "not yet mentioned" queue) only
5. ⬜ Module 3 (technical audit) — DB table + read-only API + placeholder UI only
6. ⬜ Module 5 (Reddit monitor) — DB table + read/update API (status bookkeeping works) + UI only
7. ⬜ Scheduling/automation layer — the `app/scheduler` seam exists, no jobs registered yet
8. ⬜ Dashboard polish pass

## Architecture decisions

Every judgment call made without asking is logged in [`docs/DECISIONS.md`](docs/DECISIONS.md), including
why. Worth reading before extending this — in particular #4 (the Claude model id in the brief isn't real,
it's a config value now) and #9 (the FastAPI backend should not be deployed as Vercel serverless functions).
