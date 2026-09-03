from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import articles, audit, auth, geo, health, keywords, reddit, sites
from app.core.auth import require_auth
from app.core.config import get_settings
from app.scheduler import jobs
from app.scheduler.scheduled_jobs import run_weekly_audits, run_weekly_geo_checks


@asynccontextmanager
async def lifespan(app: FastAPI):
    jobs.start()
    # Runs inside this process — no external cron, nothing else to set up.
    # Staggered an hour apart so they don't compete for the same rate limits.
    jobs.add_cron_job(run_weekly_audits, job_id="weekly_audit", day_of_week="mon", hour=3)
    jobs.add_cron_job(run_weekly_geo_checks, job_id="weekly_geo_check", day_of_week="mon", hour=4)
    yield
    jobs.shutdown()


app = FastAPI(title="GrowthPilot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_allowed_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

# health and auth/login are the only unauthenticated routes — everything
# else requires the bearer token issued by POST /api/auth/login.
app.include_router(health.router)
app.include_router(auth.router)

_protected = [Depends(require_auth)]
app.include_router(sites.router, dependencies=_protected)
app.include_router(keywords.router, dependencies=_protected)
app.include_router(articles.router, dependencies=_protected)
app.include_router(audit.router, dependencies=_protected)
app.include_router(geo.router, dependencies=_protected)
app.include_router(reddit.router, dependencies=_protected)
