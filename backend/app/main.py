from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import articles, audit, geo, health, keywords, reddit, sites
from app.scheduler import jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    jobs.start()
    yield
    jobs.shutdown()


app = FastAPI(title="GrowthPilot API", lifespan=lifespan)

# Local dev only — the Vite dev server runs on :3100 (docs/DECISIONS.md #11).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3100"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sites.router)
app.include_router(keywords.router)
app.include_router(articles.router)
app.include_router(audit.router)
app.include_router(geo.router)
app.include_router(reddit.router)
