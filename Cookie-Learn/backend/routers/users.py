
# User profile management routes: update profile, upload avatar, set language, refill hearts
import base64
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import UpdateProfileRequest, UserOut
from security import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

AVATAR_DIR = Path(__file__).resolve().parent.parent / "static" / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)


@router.patch("/me", response_model=UserOut)
def update_me(body: UpdateProfileRequest, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Update the current user's profile fields (username, name, bio, avatar, settings)
    if body.username and body.username != current.username:
        if db.query(User).filter(User.username == body.username).first():
            raise HTTPException(status_code=400, detail="This username is already taken")
        current.username = body.username
    if body.full_name is not None:
        current.full_name = body.full_name
    if body.bio is not None:
        current.bio = body.bio
    if body.avatar_url is not None:
        current.avatar_url = body.avatar_url
    if body.native_language_code is not None:
        current.native_language_code = body.native_language_code.lower()
    if body.daily_goal_xp is not None and 10 <= body.daily_goal_xp <= 200:
        current.daily_goal_xp = body.daily_goal_xp
    if body.level_code is not None and body.level_code in {"A1", "A2", "B1", "B2", "C1", "C2"}:
        current.level_code = body.level_code
    db.commit()
    db.refresh(current)
    return UserOut.model_validate(current)


@router.post("/me/avatar", response_model=UserOut)
async def upload_avatar(file: UploadFile = File(...), current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Upload and save an avatar image for the current user
    if file.content_type not in {"image/png", "image/jpeg", "image/webp", "image/gif"}:
        raise HTTPException(status_code=400, detail="Invalid file type")
    ext = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/gif": "gif"}[file.content_type]
    fname = f"{uuid.uuid4().hex}.{ext}"
    fpath = AVATAR_DIR / fname
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File cannot be larger than 5MB")
    fpath.write_bytes(content)
    current.avatar_url = f"/static/avatars/{fname}"
    db.commit()
    db.refresh(current)
    return UserOut.model_validate(current)


@router.post("/me/active-language", response_model=UserOut)
def set_active_language(code: str, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Set which language the user is currently learning
    current.active_language_code = code.lower()
    db.commit()
    db.refresh(current)
    return UserOut.model_validate(current)


@router.post("/me/refill-hearts", response_model=UserOut)
def refill_hearts(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Refill hearts using gems (cost: 10 gems per missing heart)
    if current.hearts >= current.max_hearts:
        return UserOut.model_validate(current)
    cost = (current.max_hearts - current.hearts) * 10
    if current.gems < cost:
        raise HTTPException(status_code=400, detail="Insufficient gems")
    current.gems -= cost
    current.hearts = current.max_hearts
    db.commit()
    db.refresh(current)
    return UserOut.model_validate(current)
