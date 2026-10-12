
# Progress tracking routes: submit answers, complete lessons, manage daily quests, refresh state
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from gamification import (
    add_xp, bump_quest, check_achievements, refresh_daily_quests,
    regen_hearts, reset_daily_if_needed, reset_weekly_league_if_needed, update_streak,
)
from models import DailyQuest, User, UserAnswer, UserLessonProgress
from schemas import (
    AchievementOut, AnswerSubmit, DailyQuestOut, LessonCompleteRequest,
    LessonCompleteResponse, UserOut,
)
from security import get_current_user

router = APIRouter(prefix="/progress", tags=["progress"])


@router.post("/answer")
def submit_answer(body: AnswerSubmit, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Record a single answer submission and deduct a heart if incorrect
    regen_hearts(current)
    if current.hearts <= 0:
        db.commit()
        raise HTTPException(status_code=402, detail="You have no hearts left. Refill with gems or wait.")
    ans = UserAnswer(
        user_id=current.id,
        lesson_id=body.lesson_id,
        question_type=body.question_type,
        prompt=body.prompt,
        user_answer=body.user_answer,
        correct_answer=body.correct_answer,
        is_correct=body.is_correct,
        language_code=body.language_code,
        topic=body.topic,
    )
    db.add(ans)
    if not body.is_correct and current.hearts > 0:
        current.hearts = max(0, current.hearts - 1)
    db.commit()
    return {"hearts": current.hearts}


@router.post("/complete-lesson", response_model=LessonCompleteResponse)
def complete_lesson(body: LessonCompleteRequest, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Mark a lesson as completed, calculate XP, update streak, check quests and achievements
    regen_hearts(current)
    reset_daily_if_needed(current)
    reset_weekly_league_if_needed(current)

    accuracy = body.correct_count / body.total_count if body.total_count else 0.0
    base_xp = 10
    perfect_bonus = 5 if accuracy >= 0.999 else 0
    speed_bonus = 5 if 0 < body.duration_seconds <= 120 else 0
    earned = base_xp + perfect_bonus + speed_bonus + max(0, body.correct_count - body.total_count // 2)

    leveled_up = add_xp(current, earned)
    update_streak(current)

    prog = (
        db.query(UserLessonProgress)
        .filter(UserLessonProgress.user_id == current.id, UserLessonProgress.lesson_id == body.lesson_id)
        .first()
    )
    if not prog:
        prog = UserLessonProgress(user_id=current.id, lesson_id=body.lesson_id)
        db.add(prog)
    prog.completed = True
    prog.attempts = (prog.attempts or 0) + 1
    prog.best_accuracy = max(prog.best_accuracy or 0.0, accuracy)
    prog.best_xp = max(prog.best_xp or 0, earned)
    prog.completed_at = datetime.now(timezone.utc)

    refresh_daily_quests(db, current)
    bump_quest(db, current, "earn_xp", earned)
    bump_quest(db, current, "complete_lessons", 1)
    if accuracy >= 0.999:
        bump_quest(db, current, "perfect_lesson", 1)

    new_ach = check_achievements(db, current)
    db.commit()
    db.refresh(current)
    return LessonCompleteResponse(
        xp_earned=earned,
        streak_days=current.streak_days,
        daily_xp_earned=current.daily_xp_earned,
        daily_goal_xp=current.daily_goal_xp,
        new_level=leveled_up,
        new_achievements=[AchievementOut.model_validate(a) for a in new_ach],
        hearts=current.hearts,
    )


@router.get("/daily-quests", response_model=List[DailyQuestOut])
def daily_quests(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get or create today's daily quests for the current user
    quests = refresh_daily_quests(db, current)
    db.commit()
    return [DailyQuestOut.model_validate(q) for q in quests]


@router.get("/state", response_model=UserOut)
def refreshed_state(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Return the user's full state with heart regen and daily/weekly resets applied
    regen_hearts(current)
    reset_daily_if_needed(current)
    reset_weekly_league_if_needed(current)
    db.commit()
    db.refresh(current)
    return UserOut.model_validate(current)
