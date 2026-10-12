"""
Translation repository.

Encapsulates all direct database access for the `Translation` model.
"""

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.translation import Translation


class TranslationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, translation: Translation) -> Translation:
        self._session.add(translation)
        await self._session.flush()
        await self._session.refresh(translation)
        return translation

    async def get_paginated_by_user(
        self, user_id: uuid.UUID, page: int, page_size: int
    ) -> tuple[list[Translation], int]:
        count_result = await self._session.execute(
            select(func.count(Translation.id)).where(Translation.user_id == user_id)
        )
        total_items = count_result.scalar_one()

        offset = (page - 1) * page_size
        result = await self._session.execute(
            select(Translation)
            .where(Translation.user_id == user_id)
            .order_by(Translation.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(result.scalars().all())
        return items, total_items

    async def delete_all_by_user(self, user_id: uuid.UUID) -> None:
        await self._session.execute(delete(Translation).where(Translation.user_id == user_id))
