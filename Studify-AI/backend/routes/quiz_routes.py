from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..database import get_db
from ..dependencies import get_current_user
from ..models import User
from ..schemas import QuizGenerateRequest, QuizResponse
from ..quota_service import check_quota, increment_quota, get_limits
from ..gemini_service import gemini_service
from ..gamification_service import add_xp

router = APIRouter()

@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(req: QuizGenerateRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not await check_quota(current_user.id, "quiz_count", current_user.plan_type, db):
        limit = get_limits(current_user.plan_type)["quiz_count"]
        raise HTTPException(status_code=429, detail={"error": "quota_exceeded", "quota_type": "quiz_count", "limit": limit, "plan_type": current_user.plan_type})
        
    questions = await gemini_service.generate_quiz(req.subject, req.grade_level, req.topic, req.question_count)
    
    await increment_quota(current_user.id, "quiz_count", db)
    xp_data = await add_xp(current_user.id, 35, db)
    
    return {
        "questions": questions,
        "subject": req.subject,
        "topic": req.topic,
        "xp_notification": xp_data
    }
