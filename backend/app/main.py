from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.export import router as export_router
from app.api.gps import router as gps_router
from app.api.incidents import router as incidents_router
from app.api.lpb import router as lpb_router
from app.api.oauth import router as oauth_router
from app.api.reports import router as reports_router
from app.api.safety import router as safety_router
from app.api.search import router as search_router
from app.api.teams import router as teams_router
from app.api.users import router as users_router
from app.db.connection import close_pool, get_pool


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await get_pool()
    yield
    await close_pool()


app = FastAPI(
    title="SearchParty",
    description="Search and Rescue coordination API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(oauth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(incidents_router, prefix="/api/v1")
app.include_router(teams_router, prefix="/api/v1")
app.include_router(gps_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(lpb_router, prefix="/api/v1")
app.include_router(safety_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
