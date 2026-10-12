
# Statistics routes: user stats overview, achievement list
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from gamification import today_utc
from models import Achievement, User, UserAchievement, UserAnswer, UserLessonProgress
from schemas import AchievementOut, DailyXPPoint, UserStats
from security import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/me", response_model=UserStats)
def my_stats(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Compute and return comprehensive stats for the current user
    lessons_completed = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == current.id, UserLessonProgress.completed == True
    ).count()

    total_answers = db.query(UserAnswer).filter(UserAnswer.user_id == current.id).count()
    correct_answers = db.query(UserAnswer).filter(UserAnswer.user_id == current.id, UserAnswer.is_correct == True).count()
    accuracy = (correct_answers / total_answers) if total_answers else 0.0

    words_learned = (
        db.query(func.count(func.distinct(UserAnswer.correct_answer)))
        .filter(UserAnswer.user_id == current.id, UserAnswer.is_correct == True)
        .scalar()
        or 0
    )

    # Build daily XP data for the last 14 days
    end = today_utc()
    start = end - timedelta(days=13)
    rows = (
        db.query(func.date(UserAnswer.created_at).label("d"), func.count(UserAnswer.id))
        .filter(UserAnswer.user_id == current.id, UserAnswer.is_correct == True, func.date(UserAnswer.created_at) >= start)
        .group_by("d")
        .all()
    )
    by_day = {r[0]: int(r[1]) * 2 for r in rows}
    points: List[DailyXPPoint] = []
    d = start
    while d <= end:
        points.append(DailyXPPoint(date=d, xp=by_day.get(d, 0)))
        d = d + timedelta(days=1)

    return UserStats(
        xp_total=current.xp_total,
        streak_days=current.streak_days,
        longest_streak=current.longest_streak,
        lessons_completed=lessons_completed,
        words_learned=int(words_learned),
        accuracy=accuracy,
        total_answers=total_answers,
        correct_answers=correct_answers,
        daily_xp=points,
        level_code=current.level_code,
        league_tier=current.league_tier,
        league_xp_week=current.league_xp_week,
    )


@router.get("/achievements", response_model=List[AchievementOut])
def my_achievements(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Return all achievements with their unlock status for the current user
    unlocked = {
        ua.achievement_id: ua for ua in db.query(UserAchievement).filter(UserAchievement.user_id == current.id).all()
    }
    all_ach = db.query(Achievement).order_by(Achievement.condition_type, Achievement.condition_value).all()
    out: List[AchievementOut] = []
    for a in all_ach:
        item = AchievementOut.model_validate(a)
        if a.id in unlocked:
            item.unlocked = True
            item.unlocked_at = unlocked[a.id].unlocked_at
        out.append(item)
    return out
