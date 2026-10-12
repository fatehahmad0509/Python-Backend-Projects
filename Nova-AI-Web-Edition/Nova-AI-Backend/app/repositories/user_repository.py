"""Data access layer for the User model."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Encapsulates all direct database access for users."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_id(self, user_id: str | uuid.UUID) -> User | None:
        try:
            uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        except ValueError:
            return None
        result = await self._db.execute(select(User).where(User.id == uid))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def create(self, email: str, password_hash: str) -> User:
        user = User(email=email.lower(), password_hash=password_hash)
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def update_password(self, user: User, new_password_hash: str) -> User:
        user.password_hash = new_password_hash
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def update_details(self, user: User, details: str) -> User:
        user.details = details or None
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self._db.delete(user)
        await self._db.commit()
