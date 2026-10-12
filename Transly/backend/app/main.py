"""
Transly - application entrypoint.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.database.base import Base
from app.database.session import engine
from app.exceptions.handlers import register_exception_handlers
from app.middlewares.blocked_user import BlockedUserMiddleware
from app.middlewares.rate_limit import RateLimitMiddleware
from app.routers import auth, translations, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.DEBUG)

    if settings.AUTO_CREATE_TABLES:
        # Dev/first-run convenience only: creates tables that do not exist
        # yet. It never alters existing tables - schema changes are the
        # team's responsibility (no Alembic, per project requirements).
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Order matters: Starlette applies middleware in reverse of add order, so
# BlockedUserMiddleware (added last) runs first, then RateLimitMiddleware.
app.add_middleware(RateLimitMiddleware)
app.add_middleware(BlockedUserMiddleware)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(translations.router)


@app.api_route("/health", methods=["GET", "HEAD"], tags=["Health"], summary="Health check")
async def health_check() -> dict:
    return {"success": True, "message": "Transly API is running", "data": None}
