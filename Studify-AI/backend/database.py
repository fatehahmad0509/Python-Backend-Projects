from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from .config import get_settings

settings = get_settings()

# NullPool is RECOMMENDED when using NeonDB's external pooler
# NeonDB URL must contain ?sslmode=require
engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=False,
    connect_args={"ssl": "require"}
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE users ADD COLUMN xp_points INTEGER DEFAULT 0"))
    except Exception:
        pass

    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE users ADD COLUMN level INTEGER DEFAULT 1"))
    except Exception:
        pass

    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE users ADD COLUMN streak_count INTEGER DEFAULT 0"))
    except Exception:
        pass

    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE users ADD COLUMN last_action_date DATE"))
    except Exception:
        pass

    # Drop old tables to save space and remove unused features
    try:
        async with engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS summaries CASCADE"))
    except Exception:
        pass

    try:
        async with engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS quiz_results CASCADE"))
    except Exception:
        pass

    try:
        async with engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS flashcards CASCADE"))
    except Exception:
        pass

    try:
        async with engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS study_sessions CASCADE"))
    except Exception:
        pass
