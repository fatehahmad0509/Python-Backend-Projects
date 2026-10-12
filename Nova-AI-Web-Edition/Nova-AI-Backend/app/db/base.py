"""Declarative base class for all ORM models.

Deliberately does NOT import the model modules here: models import Base
from this module, so importing them back from here would create a
circular import. Anything that needs all models registered on
Base.metadata (Alembic, table creation in tests, etc.) should instead
`import app.models`, which registers every model as a side effect.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base. All models inherit from this."""
    pass
