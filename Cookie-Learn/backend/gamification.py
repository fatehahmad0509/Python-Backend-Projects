
# Gamification logic: hearts, streaks, leagues, daily quests, achievements, and XP
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session

from models import Achievement, DailyQuest, User, UserAchievement, UserLessonProgress, UserAnswer

LEAGUE_TIERS = ["bronze", "silver", "gold", "platinum", "diamond", "master"]
LEAGUE_PROMOTION_XP = {"bronze": 200, "silver": 500, "gold": 1000, "platinum": 2000, "diamond": 4000, "master": 10_000}
HEART_REGEN_MINUTES = 30


def today_utc() -> date:
    return datetime.now(timezone.utc).date()


def regen_hearts(user: User) -> None:
    # Regenerate hearts over time based on elapsed minutes since last regen
    if user.hearts >= user.max_hearts:
        user.last_heart_regen = datetime.now(timezone.utc)
        return
    if not user.last_heart_regen:
        user.last_heart_regen = datetime.now(timezone.utc)
        return
    last = user.last_heart_regen
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    elapsed_min = (datetime.now(timezone.utc) - last).total_seconds() / 60.0
    to_add = int(elapsed_min // HEART_REGEN_MINUTES)
    if to_add > 0:
        new_hearts = min(user.max_hearts, user.hearts + to_add)
        user.hearts = new_hearts
        user.last_heart_regen = datetime.now(timezone.utc)


def reset_daily_if_needed(user: User) -> None:
    # Reset daily XP counter when a new calendar day starts
    today = today_utc()
    if user.daily_reset_date != today:
        user.daily_reset_date = today
        user.daily_xp_earned = 0


def reset_weekly_league_if_needed(user: User) -> None:
    # At the start of a new week, apply promotion/relegation logic and reset weekly XP
    today = today_utc()
    monday = today - timedelta(days=today.weekday())
    if user.league_week_start != monday:
        if user.league_week_start is not None:
            promo = LEAGUE_PROMOTION_XP.get(user.league_tier, 99999)
            if user.league_xp_week >= promo:
                idx = min(len(LEAGUE_TIERS) - 1, LEAGUE_TIERS.index(user.league_tier) + 1)
                user.league_tier = LEAGUE_TIERS[idx]
            elif user.league_xp_week < promo // 4 and user.league_tier != "bronze":
                idx = max(0, LEAGUE_TIERS.index(user.league_tier) - 1)
                user.league_tier = LEAGUE_TIERS[idx]
        user.league_week_start = monday
        user.league_xp_week = 0


def update_streak(user: User) -> None:
    # Update streak: increment if active yesterday, reset to 1 if gap > 1 day
    today = today_utc()
    if user.last_active_date == today:
        return
    if user.last_active_date == today - timedelta(days=1):
        user.streak_days += 1
    else:
        user.streak_days = 1
    user.longest_streak = max(user.longest_streak, user.streak_days)
    user.last_active_date = today


def add_xp(user: User, xp: int) -> bool:
    # Add XP and return True if the user leveled up (every 100 XP)
    prev_level = user.xp_total // 100
    user.xp_total += xp
    user.daily_xp_earned += xp
    user.league_xp_week += xp
    new_level = user.xp_total // 100
    return new_level > prev_level


def refresh_daily_quests(db: Session, user: User) -> list[DailyQuest]:
    # Get today's quests for the user, creating default quests if none exist yet
    today = today_utc()
    quests = db.query(DailyQuest).filter(DailyQuest.user_id == user.id, DailyQuest.quest_date == today).all()
    if quests:
        return quests
    defaults = [
        ("earn_xp", "Earn 30 XP today", 30, 15, "Zap"),
        ("complete_lessons", "Complete 3 lessons", 3, 20, "BookOpen"),
        ("perfect_lesson", "Finish a lesson without mistakes", 1, 25, "Star"),
    ]
    quests = []
    for qtype, title, target, xp, icon in defaults:
        q = DailyQuest(
            user_id=user.id, quest_date=today, quest_type=qtype,
            title=title, target=target, progress=0, xp_reward=xp, icon=icon,
        )
        db.add(q)
        quests.append(q)
    db.flush()
    return quests


def bump_quest(db: Session, user: User, quest_type: str, amount: int) -> None:
    # Increment progress for a specific type of daily quest
    quests = refresh_daily_quests(db, user)
    for q in quests:
        if q.quest_type == quest_type and not q.completed:
            q.progress = min(q.target, q.progress + amount)
            if q.progress >= q.target:
                q.completed = True
                user.xp_total += q.xp_reward
                user.daily_xp_earned += q.xp_reward
                user.league_xp_week += q.xp_reward


def check_achievements(db: Session, user: User) -> list[Achievement]:
    # Check and unlock any achievements the user has earned but hasn't yet received
    unlocked_ids = {ua.achievement_id for ua in db.query(UserAchievement).filter(UserAchievement.user_id == user.id).all()}
    all_achievements = db.query(Achievement).all()
    new_unlocks: list[Achievement] = []

    lessons_completed = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == user.id, UserLessonProgress.completed == True
    ).count()
    perfect_lessons = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == user.id, UserLessonProgress.best_accuracy >= 0.999
    ).count()
    total_correct = db.query(UserAnswer).filter(UserAnswer.user_id == user.id, UserAnswer.is_correct == True).count()

    for ach in all_achievements:
        if ach.id in unlocked_ids:
            continue
        cond = False
        if ach.condition_type == "streak":
            cond = user.streak_days >= ach.condition_value
        elif ach.condition_type == "xp":
            cond = user.xp_total >= ach.condition_value
        elif ach.condition_type == "lessons":
            cond = lessons_completed >= ach.condition_value
        elif ach.condition_type == "perfect_lessons":
            cond = perfect_lessons >= ach.condition_value
        elif ach.condition_type == "words":
            cond = total_correct >= ach.condition_value
        if cond:
            db.add(UserAchievement(user_id=user.id, achievement_id=ach.id))
            user.xp_total += ach.xp_reward
            new_unlocks.append(ach)
    return new_unlocks
