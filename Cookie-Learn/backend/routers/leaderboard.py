
# Leaderboard route: show weekly rankings within the user's league tier
from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from gamification import today_utc
from models import User
from schemas import LeaderboardEntry, LeaderboardOut
from security import get_current_user

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("", response_model=LeaderboardOut)
def leaderboard(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get the top 30 users in the same league tier as the current user, sorted by weekly XP
    today = today_utc()
    monday = today - timedelta(days=today.weekday())
    rows = (
        db.query(User)
        .filter(User.league_tier == current.league_tier)
        .order_by(User.league_xp_week.desc(), User.xp_total.desc())
        .limit(30)
        .all()
    )
    entries = []
    my_rank = None
    for idx, u in enumerate(rows, start=1):
        entries.append(LeaderboardEntry(
            user_id=u.id, username=u.username, avatar_url=u.avatar_url,
            xp_week=u.league_xp_week, streak_days=u.streak_days, rank=idx,
        ))
        if u.id == current.id:
            my_rank = idx
    return LeaderboardOut(tier=current.league_tier, week_start=monday, entries=entries, my_rank=my_rank)
