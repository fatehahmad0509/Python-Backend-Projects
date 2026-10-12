from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..database import get_db
from ..dependencies import get_current_user
from ..models import User
from ..schemas import SummaryRequest, SummaryResponse
from ..quota_service import check_quota, increment_quota, get_limits
from ..gemini_service import gemini_service
from ..gamification_service import add_xp

router = APIRouter()

@router.post("/create", response_model=SummaryResponse)
async def create_summary(req: SummaryRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not await check_quota(current_user.id, "summary_count", current_user.plan_type, db):
        limit = get_limits(current_user.plan_type)["summary_count"]
        raise HTTPException(status_code=429, detail={"error": "quota_exceeded", "quota_type": "summary_count", "limit": limit, "plan_type": current_user.plan_type})
        
    result = await gemini_service.summarize_content(req.content, req.content_type)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    await increment_quota(current_user.id, "summary_count", db)
    xp_data = await add_xp(current_user.id, 10, db)
    return {
        "title": result.get("title", "Özet"),
        "content": result.get("content", ""),
        "xp_notification": xp_data
    }
