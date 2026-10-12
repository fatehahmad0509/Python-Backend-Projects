from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..dependencies import get_current_user
from ..models import User
from ..schemas import CoachMessage, CoachResponse
from ..quota_service import check_quota, increment_quota, get_limits
from ..gemini_service import gemini_service
from ..gamification_service import add_xp

router = APIRouter()

@router.post("/chat", response_model=CoachResponse)
async def chat(req: CoachMessage, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not await check_quota(current_user.id, "ai_coach_count", current_user.plan_type, db):
        limit = get_limits(current_user.plan_type)["ai_coach_count"]
        raise HTTPException(status_code=429, detail={"error": "quota_exceeded", "quota_type": "ai_coach_count", "limit": limit, "plan_type": current_user.plan_type})
        
    reply = await gemini_service.chat_coach(req.message, req.history)
    
    await increment_quota(current_user.id, "ai_coach_count", db)
    xp_data = await add_xp(current_user.id, 10, db)
    
    return {"reply": reply, "xp_notification": xp_data}
