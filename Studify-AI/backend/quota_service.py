from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import Quota

LIMITS = {
    "FREE": {
        "flashcard_count": 5,
        "image_upload_count": 3,
        "ai_coach_count": 10,
        "quiz_count": 1,
        "summary_count": 3
    },
    "PLUS": {
        "flashcard_count": 25,
        "image_upload_count": 15,
        "ai_coach_count": 50,
        "quiz_count": 10,
        "summary_count": 15
    }
}

def get_limits(plan_type: str) -> dict:
    return LIMITS.get(plan_type, LIMITS["FREE"])

async def get_or_create_quota(user_id: int, db: AsyncSession) -> Quota:
    today = date.today()
    result = await db.execute(select(Quota).where(Quota.user_id == user_id, Quota.date == today))
    quota = result.scalars().first()
    
    if not quota:
        quota = Quota(user_id=user_id, date=today)
        db.add(quota)
        await db.commit()
        await db.refresh(quota)
        
    # Delete old quotas (older than 2 days) to save space
    from datetime import timedelta
    from sqlalchemy import delete
    two_days_ago = today - timedelta(days=2)
    try:
        await db.execute(delete(Quota).where(Quota.date < two_days_ago))
        await db.commit()
    except Exception:
        pass

    return quota

async def check_quota(user_id: int, quota_type: str, plan_type: str, db: AsyncSession) -> bool:
    quota = await get_or_create_quota(user_id, db)
    limits = get_limits(plan_type)
    
    current_count = getattr(quota, quota_type, 0)
    limit = limits.get(quota_type, 0)
    
    return current_count < limit

async def increment_quota(user_id: int, quota_type: str, db: AsyncSession) -> None:
    quota = await get_or_create_quota(user_id, db)
    current = getattr(quota, quota_type, 0)
    setattr(quota, quota_type, current + 1)
    await db.commit()

async def get_quota_info(user_id: int, plan_type: str, db: AsyncSession) -> dict:
    quota = await get_or_create_quota(user_id, db)
    limits = get_limits(plan_type)
    
    return {
        "flashcard_count": quota.flashcard_count,
        "flashcard_limit": limits["flashcard_count"],
        "image_upload_count": quota.image_upload_count,
        "image_upload_limit": limits["image_upload_count"],
        "ai_coach_count": quota.ai_coach_count,
        "ai_coach_limit": limits["ai_coach_count"],
        "quiz_count": quota.quiz_count,
        "quiz_limit": limits["quiz_count"],
        "summary_count": quota.summary_count,
        "summary_limit": limits["summary_count"]
    }
