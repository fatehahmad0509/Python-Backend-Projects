# Database configuration and session management.
# Uses SQLAlchemy with a SQLite backend.
# WAL mode and foreign key support are enabled on every connection.

import os
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# Resolve the database file path relative to the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "repairhub.db")

# Create the SQLAlchemy engine with thread-safety for SQLite
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)


@event.listens_for(engine, "connect")
def _set_pragma(dbapi_connection, connection_record):
    """Enable WAL journal mode and foreign key constraints on every new connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL").fetchall()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Session factory — autocommit disabled, autoflush enabled
SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=True, expire_on_commit=False)

# Declarative base shared by all ORM models
Base = declarative_base()


def get_session():
    """Return a new database session (caller is responsible for closing it)."""
    return SessionFactory()


@contextmanager
def session_scope():
    """Context manager that automatically commits, rolls back, and closes a session.

    Usage:
        with session_scope() as s:
            CustomerService(s).delete(cid)
    """
    s = SessionFactory()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def init_db():
    """Create all database tables defined in the ORM models."""
    import models.models  # noqa: import triggers model registration on Base
    Base.metadata.create_all(engine)
