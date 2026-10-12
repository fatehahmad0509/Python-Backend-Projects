
# Authentication routes: register, login, session info, password change
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from gamification import regen_hearts, reset_daily_if_needed, reset_weekly_league_if_needed
from models import User
from schemas import (
    LoginRequest, RegisterRequest, TokenResponse, UserOut, ChangePasswordRequest,
)
from security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    # Create a new user account and return a JWT token
    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(status_code=400, detail="This email is already registered")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="This username is already taken")

    user = User(
        email=body.email.lower(),
        username=body.username,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        native_language_code=(body.native_language_code or "tr").lower(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    # Authenticate user by email/password and return a JWT token
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    regen_hearts(user)
    reset_daily_if_needed(user)
    reset_weekly_league_if_needed(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Return the currently authenticated user's profile with fresh gamification state
    regen_hearts(current)
    reset_daily_if_needed(current)
    reset_weekly_league_if_needed(current)
    db.commit()
    db.refresh(current)
    return UserOut.model_validate(current)


@router.post("/change-password")
def change_password(body: ChangePasswordRequest, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Change the current user's password after verifying the old one
    if not verify_password(body.current_password, current.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current.password_hash = hash_password(body.new_password)
    db.commit()
    return {"ok": True}
