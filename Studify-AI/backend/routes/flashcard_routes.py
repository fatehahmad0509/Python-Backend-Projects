from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..database import get_db
from ..dependencies import get_current_user
from ..models import User
from ..schemas import FlashcardGenerateRequest, FlashcardGenerateResponse
from ..quota_service import check_quota, increment_quota, get_limits
from ..gemini_service import gemini_service
from ..gamification_service import add_xp

router = APIRouter()

@router.post("/generate", response_model=FlashcardGenerateResponse)
async def generate_flashcards(req: FlashcardGenerateRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not await check_quota(current_user.id, "flashcard_count", current_user.plan_type, db):
        limit = get_limits(current_user.plan_type)["flashcard_count"]
        raise HTTPException(status_code=429, detail={"error": "quota_exceeded", "quota_type": "flashcard_count", "limit": limit, "plan_type": current_user.plan_type})
        
    cards_data = await gemini_service.generate_flashcards(req.notes_text, req.count)
    
    await increment_quota(current_user.id, "flashcard_count", db)
    xp_data = await add_xp(current_user.id, 20, db)
    return {"cards": cards_data, "xp_notification": xp_data}

@router.post("/generate-from-image", response_model=FlashcardGenerateResponse)
async def generate_from_image(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not await check_quota(current_user.id, "flashcard_count", current_user.plan_type, db):
        limit = get_limits(current_user.plan_type)["flashcard_count"]
        raise HTTPException(status_code=429, detail={"error": "quota_exceeded", "quota_type": "flashcard_count", "limit": limit, "plan_type": current_user.plan_type})
        
    image_bytes = await file.read()
    mime_type = file.content_type or "image/jpeg"
    
    extracted_text = await gemini_service.analyze_image(image_bytes, mime_type)
    cards_data = await gemini_service.generate_flashcards(extracted_text, 5)
    
    await increment_quota(current_user.id, "flashcard_count", db)
    xp_data = await add_xp(current_user.id, 20, db)
    return {"cards": cards_data, "xp_notification": xp_data}
