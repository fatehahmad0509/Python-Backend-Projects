from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..database import get_db
from ..dependencies import get_current_user
from ..models import User
from ..schemas import ProfileResponse, LeaderboardResponse
from ..quota_service import get_quota_info
from ..gamification_service import get_leaderboard
from ..gamification_service import check_streak

router = APIRouter()

@router.get("/", response_model=ProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    quotas = await get_quota_info(current_user.id, current_user.plan_type, db)
    xp_current_level = current_user.xp_points % 100
    xp_to_next_level = max(100 - xp_current_level, 1)
    await check_streak(current_user.id, db)
    return {
        "user": current_user,
        "quotas": quotas,
        "xp_current_level": xp_current_level,
        "xp_to_next_level": xp_to_next_level
    }

@router.get("/leaderboard", response_model=LeaderboardResponse)
async def leaderboard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_leaderboard(db, current_user_id=current_user.id)
