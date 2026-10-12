from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..dependencies import get_current_user
from ..models import User
from ..schemas import SolverResponse
from ..quota_service import check_quota, increment_quota, get_limits
from ..gemini_service import gemini_service
from ..gamification_service import add_xp

router = APIRouter()

@router.post("/solve", response_model=SolverResponse)
async def solve_question(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not await check_quota(current_user.id, "image_upload_count", current_user.plan_type, db):
        limit = get_limits(current_user.plan_type)["image_upload_count"]
        raise HTTPException(status_code=429, detail={"error": "quota_exceeded", "quota_type": "image_upload_count", "limit": limit, "plan_type": current_user.plan_type})
        
    image_bytes = await file.read()
    mime_type = file.content_type or "image/jpeg"
    
    result = await gemini_service.solve_question(image_bytes, mime_type)
    
    await increment_quota(current_user.id, "image_upload_count", db)
    xp_data = await add_xp(current_user.id, 15, db)
    result["xp_notification"] = xp_data
    return result
