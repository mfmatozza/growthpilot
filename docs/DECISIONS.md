# Architecture decisions

Judgment calls made without asking, and why. Revisit any of these if they stop fitting.

## 1. Package manager: plain `requirements.txt`, not Poetry/PDM
Keeps the Docker image simple and avoids a lockfile toolchain for a project that starts single-maintainer.
Revisit if dependency conflicts get painful.

## 2. Migrations: SQLAlchemy 2.0 + Alembic from day one, even for a single-site local DB
Schema will change constantly across modules 1-5; hand-editing `create_all` state is a trap. Alembic is
set up now so it's not a mid-project migration itself.

## 3. Crawler: `httpx` + BeautifulSoup as the default, Playwright behind the same interface but not wired up
Most marketing/blog sites are server-rendered enough for httpx+bs4, and it avoids shipping a Chromium
binary in the base Docker image. `app/services/crawler/` defines a `PageFetcher` interface with an
`HttpxFetcher` implementation; a `PlaywrightFetcher` can be dropped in later for JS-heavy sites without
touching pipeline code. If your target site is a heavy SPA, say so and I'll wire Playwright in now.

## 4. Claude model id is a config value, not a hardcoded string — and the default is NOT `claude-sonnet-4-6`
The brief specifies `claude-sonnet-4-6`, which is not a real Anthropic model id as of this build (current
generation is the Claude 5 family / Haiku 4.5). Rather than hardcode a guess, `CLAUDE_MODEL` is an env var
(default `claude-sonnet-5`) read by `app/services/llm/anthropic_client.py`. Change it in `.env` to whatever
id you actually want — no code change needed.

## 5. Scheduling: APScheduler wrapped behind a minimal `JobScheduler` interface
`app/scheduler/` exposes `add_job`/`run_now`/`list_jobs` on top of APScheduler's `BackgroundScheduler`.
Pipelines never import APScheduler directly — they register a callable with the interface. Swapping in
Celery + Redis later means writing one new adapter, not touching Modules 1-5.

## 6. Multi-site seam: a `sites` table exists from the start, everything else has `site_id`
Single-site mode just means "there is one row in `sites`". `keywords`, `articles`, `audit_findings`,
`geo_mentions`, `reddit_opportunities` all FK to `sites.id`. This costs nothing now and avoids a painful
retrofit later.

## 7. No auth on the dashboard yet
This is a local, self-hosted internal tool talking to a backend on localhost. Skipping auth for now.
**Before deploying anywhere reachable off your machine, this needs at minimum HTTP basic auth or a
reverse-proxy auth layer** — flagging so it doesn't get forgotten.

## 8. Frontend: Vite + React + Tailwind (SPA), not Next.js
The brief's Vercel target is a hosting choice, not a framework requirement — a plain Vite SPA deploys to
Vercel fine (static build + Vercel's Vite preset) and keeps the frontend decoupled from the Python backend.
No serverless API routes are used on the frontend side; the FastAPI backend is the only API.

## 9. FastAPI backend is NOT deployed as Vercel serverless functions
APScheduler needs a long-lived process to hold its in-memory job store and run cron jobs; Vercel serverless
functions are stateless and spun down between invocations, so a scheduler can't live there. Recommended
split: frontend (static SPA) on Vercel, backend + Postgres on a persistent host (Railway, Fly.io, a VPS, or
just Docker Compose on your own box) — explicitly not Supabase, per the brief. Flagging this now so it's
not a surprise at deploy time.

## 10. DataForSEO over SerpAPI/Ahrefs API/Semrush API for keyword data
Pay-per-call with no minimum subscription, which matches the "usage-based, no recurring SaaS" constraint
better than the alternatives. SerpAPI is still used for Module 2's SERP-structure scraping (different job:
live top-10 page content, not volume/difficulty numbers) since DataForSEO's SERP endpoints are pricier for
that use case.

## 11. Local dev port 3100 applies to the frontend only
The brief's "everything on 3100" instruction is a frontend dev-server convention from the portfolio project.
The FastAPI backend runs on 8000 (Docker Compose maps it as `8000:8000`) since nothing said otherwise and
8000 is FastAPI's own convention; the frontend's Vite dev server proxies `/api` to it. Say the word if you
want the backend on a different port too.

## 12. Postgres host port is 5434, not 5432
This machine already has another project's Postgres container bound to `localhost:5432`. Docker Compose
maps GrowthPilot's `db` service to host port 5434 instead (container-internal port is still 5432, so this
only affects connections from your host machine, e.g. a local non-Docker `uvicorn` or a GUI DB client).

## 13. Login is a client-side UX gate, not real authentication
Per explicit request: a public marketing homepage (`/`) with a plain email/password form at `/login` that
accepts anything and sets a `localStorage` flag, gating `/dashboard/*` via a `RequireAuth` route wrapper
(`frontend/src/components/RequireAuth.tsx`, `frontend/src/auth.ts`). This is **not security** — it doesn't
touch the backend, which still has no auth of its own (decision #7). Clearing localStorage or just calling
the API directly bypasses it entirely. Fine for a single-operator internal tool; revisit before giving
anyone else access.

## 14. Both frontend and backend deploy to Railway, not Vercel + Railway
Supersedes decision #9's split recommendation, per explicit request. Railway runs long-lived containers
(unlike Vercel serverless functions), so it has no issue hosting APScheduler's persistent process — this
also simplifies decision #9's original concern. See README's Railway section for the two-service setup
(monorepo: `backend/` and `frontend/` each deploy from their own Dockerfile) and Postgres via Railway's
plugin.

## 15. Default LLM provider is OpenAI, not Anthropic — and the model is gpt-4o, not gpt-5
Per explicit request. `LLM_PROVIDER` (default `openai`) picks between `OpenAIClient` and `AnthropicClient`
via `app/services/llm/factory.py` — every pipeline/route calls `get_default_llm_client()`, never a provider
class directly, so this is a one-line env var change, not a code change. `OPENAI_MODEL` is a config value for
the same reason as decision #4. Tried `gpt-5` first: it spends hidden "reasoning" tokens out of
`max_completion_tokens` before emitting visible content, and on the keyword-candidates prompt (asks for
30-50 structured items) reasoning consumed the entire 4096-token budget, returning empty content — confirmed
against the real API, not a guess. `gpt-4o` has no reasoning tax, is cheaper, and reliably returns the full
list. Reconsider a reasoning model for prompts that actually need deep reasoning (e.g. Module 2 outlining),
but verify against the real API with a realistically-sized prompt first, not a toy one.

## 16. Real server-side login, not a client-side gate — supersedes #13
Per explicit request ("don't let a@a / a work"). `POST /api/auth/login` checks email+password against
`ADMIN_EMAIL`/`ADMIN_PASSWORD` (plaintext env-var comparison — there's exactly one account, so a user table
and password hashing would be complexity with no payoff) and returns `SECRET_KEY` itself as the bearer
token; every other `/api/*` route (`/health` and `/api/auth/login` excepted) requires
`Authorization: Bearer <token>` via the `require_auth` dependency in `app/core/auth.py`, wired per-router in
`app/main.py`. The frontend still keeps a token in `localStorage` and gates `/dashboard/*` client-side
(`RequireAuth`), but that's now just a UX nicety on top of a real server-side check, not the only check.

## 17. Multi-site is route-scoped: `/dashboard/sites/:siteId/...`
Per explicit request for separate per-site dashboards. `/dashboard` is now a site picker/creator
(`SitesHome.tsx`) rather than a single global view; every module page reads `siteId` from the route and
filters its API calls by it (`?site_id=`, already supported by every list endpoint). `Keywords.tsx` no
longer owns its own site dropdown/create-site form — that moved to `SitesHome.tsx`, the one place "add a
website" happens now.

## 18. Dashboard accent palette: a validated pastel green + pastel blue pair
Per explicit request to drop the navy/blue. Chose via the `dataviz` skill's validator rather than eyeballing
it: mark/accent hues `#0DA678` (green) and `#2A9BE0` (blue) pass CVD-separation and lightness-band checks
(`node scripts/validate_palette.js "#0DA678,#2A9BE0" --mode light`); lighter tints of the same hues
(`brand.greenSoft`/`brand.blueSoft`/`*Tint`, see `frontend/tailwind.config.js`) are used for backgrounds/chips
where a true pastel reads fine because they're not carrying a thin data-mark against white.

## 19. Technical audit findings are a full snapshot each run, not diffed against prior wording
Module 3's LLM summarization step rewrites each finding's description in its own words every run, so
fuzzy-matching descriptions across runs to preserve `first_seen` continuity for a persisting issue isn't
reliable without adding a stable key column (a real migration, deferred). Instead, each run marks every
previously-open finding for the site resolved, then inserts a fresh set. Correct for "what's open right
now, ranked by severity" (the actual UI need); loses "how long has this specific issue been open" — revisit
if that history starts to matter, by adding a deterministic `raw_key` (page + check category) column and
diffing on that instead of on the LLM's prose.

## 20. GEO/audit "run now" is synchronous; weekly runs are wired via APScheduler in-process
Per explicit request that automation not require "switching to another website" — `run_weekly_audits`/
`run_weekly_geo_checks` (`app/scheduler/scheduled_jobs.py`) run inside the same backend process Railway
already keeps alive (decision #14 is what makes this possible — a serverless backend couldn't hold
APScheduler's job store). Each site is wrapped in its own try/except so one bad site doesn't kill the run
for the rest. Manual "run now" buttons hit the same pipelines synchronously (same tradeoff as Module 1's
`/api/keywords/research` — acceptable for a single-user tool, revisit if a run starts taking long enough to
risk an HTTP timeout).

## 21. GEO tracker's target queries are approved keywords directly, not a separate query list
The brief allows either "seeded from Module 1's keyword list, or manually added." Built only the seeding
path — a separate queries CRUD is a real feature with its own UI, deferred rather than half-built. Capped
at the top 10 approved keywords by opportunity score per run, per site, to bound cost/latency on both the
manual and scheduled paths (each query costs one answer call + one analysis call, per provider).

## 22. Gemini and Perplexity clients are minimal, hand-rolled — not new SDKs
Gemini: a small `httpx` REST wrapper against the Generative Language API, not the `google-generativeai`
package — avoids a new heavy dependency for the one thing Module 4 needs (ask a question, get text back).
Perplexity: its API is OpenAI-compatible, so `PerplexityClient` just points the existing `openai` SDK at
`https://api.perplexity.ai` instead of writing a second HTTP client from scratch. Neither implements
`complete_json` (raises `NotImplementedError`) — nothing in this codebase asks either of them for structured
output yet; add it if that changes rather than guessing at the shape now.

## 23. Keyword generation is biased toward long-tail phrases, and dedupes against prior runs
Per explicit request ("long tail ones are what get you found"). `_KEYWORD_CANDIDATES_SYSTEM` now asks for
at least two-thirds long-tail (4+ word) phrases explicitly, with the reasoning stated in the prompt itself
(head terms need domain authority a smaller site doesn't have) rather than just an instruction — verified
against the real API: 43/43 candidates came back 4+ words on one real run. Separately, repeated runs on the
same site were piling up near-duplicate candidates (confirmed on a real site: 54 candidates after a few
runs, many overlapping in theme) because nothing told the model what already existed. Existing keyword text
is now listed in the prompt ("don't repeat these"), capped at 200 to bound prompt size, plus a real
case-insensitive `dedupe_against_existing()` pass after generation as a backstop — the model mostly listens,
but the pipeline doesn't rely on that alone.
