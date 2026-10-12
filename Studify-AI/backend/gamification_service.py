from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import User

XP_PER_LEVEL = 100

async def check_streak(user_id: int, db: AsyncSession) -> dict:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        return {}

    today = date.today()

    if user.last_action_date:
        days_diff = (today - user.last_action_date).days
        if days_diff == 0:
            pass
        elif days_diff == 1:
            user.streak_count = (user.streak_count or 0) + 1
        else:
            user.streak_count = 0
    else:
        user.streak_count = 0

    user.last_action_date = today

    await db.commit()
    await db.refresh(user)

    return {"streak_count": user.streak_count}


async def add_xp(user_id: int, xp_amount: int, db: AsyncSession) -> dict:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        return {}

    old_level = user.level
    today = date.today()

    if user.last_action_date:
        days_diff = (today - user.last_action_date).days
        if days_diff == 0:
            pass
        elif days_diff == 1:
            user.streak_count = (user.streak_count or 0) + 1
        else:
            user.streak_count = 1
    else:
        user.streak_count = 1

    user.last_action_date = today
    user.xp_points = (user.xp_points or 0) + xp_amount
    new_level = (user.xp_points // XP_PER_LEVEL) + 1
    leveled_up = new_level > (user.level or 1)
    user.level = new_level

    await db.commit()
    await db.refresh(user)

    return {
        "xp_earned": xp_amount,
        "total_xp": user.xp_points,
        "level": user.level,
        "leveled_up": leveled_up,
        "streak_count": user.streak_count
    }


async def get_leaderboard(db: AsyncSession, limit: int = 50, current_user_id: int = None):
    result = await db.execute(
        select(User)
        .order_by(User.xp_points.desc())
        .limit(limit)
    )
    users = result.scalars().all()
    leaders = [
        {
            "rank": i + 1,
            "display_name": u.display_name,
            "xp_points": u.xp_points or 0,
            "level": u.level or 1,
            "streak_count": u.streak_count or 0
        }
        for i, u in enumerate(users)
    ]

    user_rank = None
    if current_user_id is not None:
        all_result = await db.execute(
            select(User).order_by(User.xp_points.desc())
        )
        all_users = all_result.scalars().all()
        for i, u in enumerate(all_users):
            if u.id == current_user_id:
                user_rank = i + 1
                break

    return {
        "leaders": leaders,
        "user_rank": user_rank
    }
