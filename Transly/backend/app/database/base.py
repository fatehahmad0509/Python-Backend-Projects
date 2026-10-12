"""
Declarative base for all SQLAlchemy models.

All models must inherit from `Base` so they are registered on a single
shared `MetaData` instance. This is required both for `Base.metadata.create_all`
(used only as a local/dev convenience, see core.config.AUTO_CREATE_TABLES)
and for any tooling that needs to introspect the schema.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Models are imported here (after Base is defined) purely so that they get
# registered on Base.metadata. This module must be imported before
# Base.metadata.create_all() is called anywhere in the application.
from app.models import daily_usage, translation, user  # noqa: E402,F401
