
# Practice (free-form test) routes: evaluate AI-graded answers, finish practice sessions
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import ai_service
from database import get_db
from gamification import (
    add_xp, bump_quest, check_achievements, refresh_daily_quests,
    regen_hearts, reset_daily_if_needed, reset_weekly_league_if_needed, update_streak,
)
from models import User, UserAnswer
from schemas import AchievementOut
from security import get_current_user

router = APIRouter(prefix="/practice", tags=["practice"])

DIFFICULTY_TO_LEVEL = {"easy": "A1", "medium": "B1", "hard": "C1"}


class EvaluateRequest(BaseModel):
    language_code: str
    level_code: Optional[str] = "A1"
    question_type: str
    prompt: str
    correct_answer: str
    user_answer: str
    topic: Optional[str] = None


class EvaluateResponse(BaseModel):
    is_correct: bool
    feedback: str
    correction: str = ""
    correct_answer: str
    hearts: int


class FinishRequest(BaseModel):
    language_code: str
    difficulty: str = "easy"
    correct_count: int
    total_count: int
    duration_seconds: int = 0


class FinishResponse(BaseModel):
    xp_earned: int
    streak_days: int
    daily_xp_earned: int
    daily_goal_xp: int
    new_level: bool = False
    new_achievements: list[AchievementOut] = []
    hearts: int
    accuracy: float


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate(body: EvaluateRequest, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Evaluate a practice answer using AI (or exact match for word_match), deduct heart if wrong
    regen_hearts(current)
    if current.hearts <= 0:
        db.commit()
        raise HTTPException(status_code=402, detail="You have no hearts left. Refill with gems or wait.")

    if body.question_type in {"word_match"}:
        is_correct = body.user_answer.strip().lower() == body.correct_answer.strip().lower()
        feedback = "Correct!" if is_correct else f"Correct answer: {body.correct_answer}"
        correction = "" if is_correct else body.correct_answer
    else:
        try:
            result = ai_service.evaluate_answer(
                language_code=body.language_code,
                level_code=body.level_code or "A1",
                question_type=body.question_type,
                prompt=body.prompt,
                correct_answer=body.correct_answer,
                user_answer=body.user_answer,
                native_language=current.native_language_code,
            )
            is_correct = bool(result.get("is_correct", False))
            feedback = result.get("feedback") or ""
            correction = result.get("correction") or ""
        except RuntimeError:
            is_correct = body.user_answer.strip().lower() == body.correct_answer.strip().lower()
            feedback = "AI could not evaluate, exact match check was performed."
            correction = "" if is_correct else body.correct_answer

    db.add(UserAnswer(
        user_id=current.id,
        lesson_id=None,
        question_type=body.question_type,
        prompt=body.prompt,
        user_answer=body.user_answer,
        correct_answer=body.correct_answer,
        is_correct=is_correct,
        language_code=body.language_code,
        topic=body.topic,
    ))
    if not is_correct and current.hearts > 0:
        current.hearts = max(0, current.hearts - 1)
    db.commit()

    return EvaluateResponse(
        is_correct=is_correct,
        feedback=feedback,
        correction=correction,
        correct_answer=body.correct_answer,
        hearts=current.hearts,
    )


@router.post("/finish", response_model=FinishResponse)
def finish(body: FinishRequest, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Complete a practice session: calculate XP with difficulty multiplier, update streak and quests
    regen_hearts(current)
    reset_daily_if_needed(current)
    reset_weekly_league_if_needed(current)

    accuracy = body.correct_count / body.total_count if body.total_count else 0.0
    diff_mult = {"easy": 1.0, "medium": 1.5, "hard": 2.0}.get(body.difficulty, 1.0)
    base = body.correct_count * 3
    perfect_bonus = 10 if accuracy >= 0.999 else 0
    speed_bonus = 5 if 0 < body.duration_seconds <= 180 else 0
    earned = int((base + perfect_bonus + speed_bonus) * diff_mult)

    leveled_up = add_xp(current, earned)
    update_streak(current)

    refresh_daily_quests(db, current)
    bump_quest(db, current, "earn_xp", earned)
    bump_quest(db, current, "complete_lessons", 1)
    if accuracy >= 0.999:
        bump_quest(db, current, "perfect_lesson", 1)

    new_ach = check_achievements(db, current)
    db.commit()
    db.refresh(current)

    return FinishResponse(
        xp_earned=earned,
        streak_days=current.streak_days,
        daily_xp_earned=current.daily_xp_earned,
        daily_goal_xp=current.daily_goal_xp,
        new_level=leveled_up,
        new_achievements=[AchievementOut.model_validate(a) for a in new_ach],
        hearts=current.hearts,
        accuracy=accuracy,
    )
