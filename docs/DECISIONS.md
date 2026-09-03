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

## 24. Module 5 (Reddit monitor) is fully built but NOT verified against the real Reddit API
Unlike every other module this session, this one couldn't be tested end-to-end before the user provided
Reddit credentials — it's built and thoroughly unit-tested against a fake client (`FakeRedditClient`), and
`prawcore`'s exception class names (`RequestException`, `ResponseException`) were confirmed to actually
exist by importing the installed package rather than assumed, but the real PRAW auth flow, search behavior,
and rate limits are unverified. Treat the first real run as the actual test, not this commit.
- Subreddits are configured per-site (`sites.subreddits`, comma-separated, editable via the existing
  `PATCH /api/sites/{id}` and a form on the Reddit tab) rather than a single global list, consistent with
  decision #17's per-site scoping.
- Target keywords reuse Module 1's approved keywords (same pattern as Module 4's #21), independently
  duplicated in `reddit_monitor.py` rather than imported from `geo_tracker.py` — small, and keeps the two
  pipelines free to diverge (e.g. different caps) without coupling.
- Read-only PRAW auth (client_id + client_secret only, no username/password) — this pipeline only ever
  reads public posts and drafts replies for a human to review; it has no code path that could post to
  Reddit even by accident.
- Wired into the weekly scheduler (#20) at hour=5, staggered after audits (3) and GEO checks (4); skipped
  entirely, per site, if that site has no subreddits configured — same graceful-skip pattern as GEO
  providers.
- Update: cross-checked the client_id+client_secret-only, no-username/password auth approach against
  developers.reddit.com's server API docs after the user pointed to them — confirmed correct for 2026 (a
  "script" app using the client_credentials grant is exactly the recommended path for read-only
  server-side monitoring). No code changes needed.

## 25. Module 2's SERP research uses SerpAPI only — no free scraper fallback, despite the brief allowing one
The brief says "SerpAPI or a scraper fallback." Tried the scraper fallback for real before deciding against
it: DuckDuckGo's HTML endpoint now returns a bot-detection challenge page (`anomaly.js`) instead of results,
and Bing serves plausible-looking but completely wrong decoy results to non-browser clients (a real test:
searching "best CRM software for small business" returned dictionary definitions of "best" and Best Buy's
homepage — deliberate scraper poisoning, not a fluke). Shipping a "fallback" that silently feeds wrong
competitor data into outline generation would be worse than no data at all. `research_competitor_structure`
returns an empty list (not an error) whenever `SERPAPI_KEY` isn't configured, and `generate_outline`'s
prompt is written to work either way — with competitor headings when available, from the model's own
knowledge of the topic otherwise. Revisit if SerpAPI's cost becomes a problem; a paid alternative (or a
proper headless-browser-based scraper, which is a much bigger lift than a simple HTTP GET) beats a fake
free one.

## 26. Article generation: no images, explicit anti-"AI-tell" instructions, real em-dash stripping
Per explicit request — images were already unbuilt (no image API key configured), so dropping them was
free; the em-dash/stock-phrase avoidance was added specifically to keep Google's AI-content signals from
tripping on generated articles. `_HUMAN_VOICE_INSTRUCTION` is appended to every outline and section-drafting
prompt (never use an em dash, avoid a named list of stock AI phrases, vary sentence length). Verified against
the real API: a full 2265-word article came back with zero em dashes without needing the backstop. That
backstop, `strip_em_dashes()`, still runs on every generated body regardless — a prompt instruction is not a
guarantee, and it costs nothing to also mechanically remove any that slip through (substitutes a comma,
which reads naturally in the large majority of real em-dash usages).
The brief's "fact-check pass... web search via Claude's tool use" is intentionally simplified to prompt-level
guidance instead: `_FACT_CHECK_NOTE` tells the model to tag any specific statistic/date/claim it isn't
highly confident about with `[VERIFY]` inline, rather than actually performing a live web search. A real
web-search-backed fact-check is a genuinely separate sub-project (hosted search tool wiring, cost, latency)
— this got the "flag things a human should double-check" value without that scope, and is flagged here so
it doesn't get mistaken for the fuller brief requirement.

## 27. Article generation is wired into weekly automation as auto-DRAFT only, never auto-publish
Per explicit request that the site "auto-updates." `run_weekly_article_drafts` (hour=6, after audits/GEO/
Reddit) finds each site's approved keywords that don't have an article yet and drafts up to 2 per site per
run — capped because an outline call plus one call per section (5-8 sections) adds up in cost/latency across
every site. Drafts land at `ArticleStatus.draft`; nothing anywhere in this codebase has a code path that
moves an article to `published` except a human clicking the status buttons in the UI (`PATCH
/api/articles/{id}`) — the brief's "give me a review UI before anything auto-publishes" is a hard
requirement, not a default that automation quietly bypasses.

## 28. The "Claude Prompt" digest tab is frontend-only, no new backend endpoint
Per explicit request for a way to hand off a week's state to a fresh Claude Code session in one paste.
Every data point it needs (candidate keywords, unpublished articles, open audit findings, GEO mentions,
new Reddit opportunities) is already served by existing site-scoped GET endpoints, so the digest is pure
client-side formatting over data already being fetched elsewhere in the app — no new API surface, nothing
new to test on the backend. Checkboxes control which sections are included; the assembled text is built
with `useMemo` and only touches `navigator.clipboard` on explicit copy, never sent anywhere on its own.
Updated in #29: the Reddit checkbox/section was removed along with the rest of the frontend Reddit surface
— see that entry.

## 29. Module 5 (Reddit) hidden from the frontend entirely — backend kept as-is, per explicit request
Reddit closed self-service OAuth app registration in late 2025 — new access now requires manual approval
under a "Responsible Builder Policy" that, per multiple independent developer reports, explicitly
deprioritizes personal/hobbyist projects (this is exactly what this project is, from Reddit's perspective).
The old unauthenticated `.json` fallback was also blocked (403) as of May 2026, so there's no free read-only
path left either — confirmed via web search, not assumed, after the user reported the registration flow no
longer working. Decision #24's entire premise (a "script" app is quick and easy to get) is no longer true.

Given a choice between (a) applying for official access anyway, (b) a paid pay-per-call third-party Reddit
data API, or (c) shelving it, the user chose to keep the backend exactly as built (pipeline, routes, models,
`PrawRedditClient`, the weekly scheduler job — all untouched, all still gracefully no-op without credentials)
but remove every trace of it from the frontend: the nav link, the route, and the Reddit checkbox/section in
the Claude Prompt digest (`Digest.tsx` no longer fetches or mentions `reddit_opportunities` at all).
`Reddit.tsx` itself is intentionally still in the repo, just unrouted — re-wiring it later is one route line
and one nav item, not a rebuild. Revisit if either Reddit's official approval comes through or a specific
third-party provider gets picked.

## 30. The Claude Prompt digest embeds real article content and concrete SEO/indexing instructions
Per explicit follow-up — the first version only listed article titles/status, which gives a receiving Claude
Code session nothing to actually publish, and no guidance on doing it in a way that's good for indexing. Now:
- Up to 3 unpublished articles get their full `body_markdown` fetched (`GET /api/articles/{id}`) and embedded
  verbatim in the prompt; anything beyond that cap is listed by title/slug with a pointer to fetch the rest,
  since embedding every draft unbounded would make the prompt unusably large.
- A publishing checklist is generated alongside embedded articles: exact slug as the URL, title/meta
  description length limits, canonical tag, Open Graph/Twitter Card tags, preserving the Markdown's heading
  hierarchy as-is, Article/BlogPosting JSON-LD, resolving every `[VERIFY]` tag before publishing (these come
  from Module 2's fact-check simplification, decision #26), keeping internal links intact, and updating the
  sitemap.
- Explicitly told not to try Google's sitemap ping endpoint — it was deprecated in 2023 — and instead to
  remind the user to request indexing per-URL via Search Console's URL Inspection tool. Getting this wrong
  (having a future session waste time on a dead endpoint, or skip indexing entirely) would undercut the
  entire point of the digest, so it's spelled out rather than assumed.
- The opening line now explicitly tells the receiving session its working directory should be the target
  site's own repo, not GrowthPilot's — this tool only ever produces content and data, it has no visibility
  into any specific website's codebase to publish into.

## 31. Articles capped well under 2000 words, per explicit request ("reaches limits" otherwise)
Earlier real runs came in at 2265-2440 words from an outline of 5-8 sections with no per-section length
guidance. Cut the outline to 4-5 sections (comparison mode: 3 options instead of an open-ended count) and
added an explicit ~100-180-word target per section plus a hard "well under 2000 words total" instruction on
both the outline and section-drafting prompts. Verified against the real API, not just assumed from the
prompt change: a real informational article came back at 932 words, a real comparison article (7 sections,
inherently longer given 3 option write-ups + intro + criteria + table + verdict) at 1290 words — both
comfortably under the limit, both still zero em dashes.
