from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import articles, audit, geo, health, keywords, reddit, sites
from app.core.config import get_settings
from app.scheduler import jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    jobs.start()
    yield
    jobs.shutdown()


app = FastAPI(title="GrowthPilot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_allowed_origins_list,
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
