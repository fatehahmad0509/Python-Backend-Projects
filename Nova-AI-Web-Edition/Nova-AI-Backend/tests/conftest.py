"""Shared pytest fixtures.

Tests run against an in-memory SQLite database (via aiosqlite) so the
suite has no external dependencies. Redis, Gemini, and SMTP calls are
faked with lightweight in-memory doubles.
"""
import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest-only")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 (registers all models on Base.metadata)
from app.db.base import Base
from app.db.session import get_db
from app.services.cache_service import CacheService, get_cache_service
from app.services.gemini_service import GeminiReply, GeminiService, get_gemini_service


class FakeCacheService(CacheService):
    """In-memory stand-in for Redis during tests."""

    def __init__(self):
        self._store: dict[str, object] = {}
        self._counters: dict[str, int] = {}

    async def get_json(self, key):
        return self._store.get(key)

    async def set_json(self, key, value, ttl_seconds=0):
        self._store[key] = value

    async def delete(self, *keys):
        for key in keys:
            self._store.pop(key, None)

    async def increment_with_expiry(self, key, window_seconds):
        self._counters[key] = self._counters.get(key, 0) + 1
        return self._counters[key]


class FakeGeminiService(GeminiService):
    """Deterministic stand-in for the Gemini API during tests.

    Always reports a fixed, predictable token usage (60 prompt + 40
    completion = 100 total) so daily-limit tests can reason about exact
    numbers without depending on real Gemini billing.
    """

    def __init__(self):
        pass

    async def generate_reply(
        self,
        history,
        new_user_message: str,
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
        user_context: str | None = None,
        web_search_allowed: bool = True,
        max_web_searches: int = 3,
    ) -> GeminiReply:
        text = f"Echo: {new_user_message}"
        if image_bytes is not None:
            text += " [saw image]"
        if user_context:
            text += f" [knows: {user_context}]"

        # Simulate Gemini deciding to use Google Search grounding when the
        # message contains a trigger word and search is allowed, so tests
        # can exercise the sources-persistence and quota-gating paths
        # without calling the real API. Also respects max_web_searches so
        # tests can exercise the per-turn quota cap.
        sources = None
        search_count = 0
        if "search" in new_user_message.lower() and web_search_allowed and max_web_searches > 0:
            sources = [{"title": "Example Source", "url": "https://example.com/article"}]
            search_count = 1

        return GeminiReply(
            text=text,
            prompt_tokens=60,
            completion_tokens=40,
            total_tokens=100,
            sources=sources,
            search_count=search_count,
        )

    async def generate_title(self, first_message: str) -> str | None:
        return f"Title: {first_message}"


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=None)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_engine):
    from app.main import app

    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    fake_cache = FakeCacheService()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_cache_service] = lambda: fake_cache
    app.dependency_overrides[get_gemini_service] = lambda: FakeGeminiService()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Attach test doubles so tests can inspect cached state without parsing HTTP responses.
        ac.fake_cache = fake_cache
        ac.session_factory = session_factory
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:10]}@example.com"


async def set_user_field(client: AsyncClient, email: str, **fields) -> None:
    """Directly update columns on a user row (bypassing the API).

    Used to simulate admin actions like blocking a user or changing
    their plan, since there are no such endpoints to exercise.
    """
    from sqlalchemy import update

    from app.models.user import User

    async with client.session_factory() as session:
        await session.execute(update(User).where(User.email == email.lower()).values(**fields))
        await session.commit()
