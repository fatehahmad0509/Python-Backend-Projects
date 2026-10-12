"""
JustLearnIt - Achievements & Stats Helper

Handles badge awarding, score-based badge checks,
per-topic statistics updates, and overall success rate recalculation.
"""
from datetime import datetime
import pytz
from core.db import get_conn

_TR = pytz.timezone("Europe/Istanbul")
def _now(): return datetime.now(_TR)


def award_badge(student_id, badge_name):
    """Award a badge to a student. Silently skips if the badge is already awarded."""
    with get_conn() as (conn, c):
        try:
            c.execute(
                "INSERT INTO student_badges(student_id,badge_name,awarded_at) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING",
                (student_id, badge_name, _now())
            )
            conn.commit()
        except:
            conn.rollback()


def check_score_badges(student_id, score, gold):
    """
    Check milestone thresholds and award the corresponding badges.
    Only awards badges the student does not already have.
    """
    with get_conn() as (conn, c):
        c.execute("SELECT badge_name FROM student_badges WHERE student_id=%s", (student_id,))
        existing = {row[0] for row in c.fetchall()}

    if (gold or 0) >= 1000 and "Gold Kid" not in existing:
        award_badge(student_id, "Gold Kid")
    if (score or 0) >= 1000 and "Rising Star" not in existing:
        award_badge(student_id, "Rising Star")
    if (score or 0) >= 5000 and "Mathematician" not in existing:
        award_badge(student_id, "Mathematician")


def update_topic_stats(student_id, topic, class_level, is_correct):
    """
    Insert or update the student's performance record for a given topic.
    Uses an upsert to increment correct/wrong/solved counters atomically.
    """
    now = _now()
    with get_conn() as (conn, c):
        try:
            c.execute("""INSERT INTO student_topic_stats(student_id,topic,class_level,total_correct,total_wrong,total_solved,last_solved_at)
                VALUES(%s,%s,%s,%s,%s,1,%s)
                ON CONFLICT(student_id,topic,class_level) DO UPDATE SET
                total_correct=student_topic_stats.total_correct+%s,
                total_wrong=student_topic_stats.total_wrong+%s,
                total_solved=student_topic_stats.total_solved+1,
                last_solved_at=%s""",
                (student_id, topic, class_level,
                 1 if is_correct else 0, 0 if is_correct else 1, now,
                 1 if is_correct else 0, 0 if is_correct else 1, now))
            conn.commit()
        except:
            conn.rollback()


def update_success_rate(student_id):
    """Recalculate and persist the student's overall success percentage."""
    with get_conn() as (conn, c):
        try:
            c.execute("""UPDATE students SET success_percentage=
                CASE WHEN total_solved>0 THEN ROUND(total_correct::NUMERIC/total_solved*100,2) ELSE 0 END
                WHERE id=%s""", (student_id,))
            conn.commit()
        except:
            conn.rollback()
