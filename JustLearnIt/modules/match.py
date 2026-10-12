"""
JustLearnIt - Match System

Handles starting a practice session (selecting questions) and submitting answers.
Supports subject-level filtering via subject_id. Answer checking is done
server-side using the stored correct_answer — never exposed to the client.
"""
import random
from datetime import datetime
import pytz
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from core.db import get_conn
from core.security import auth_required, student_required
from core.achievements import (
    award_badge, check_score_badges,
    update_topic_stats, update_success_rate
)
from core.logs import log_action

router = APIRouter(prefix="/match", tags=["Match"])

# Questions stay out of cooldown rotation for this many days
COOLDOWN_DAYS = 1
# Answered questions are kept in history for this many days
HISTORY_KEEP_DAYS = 30


class MatchStart(BaseModel):
    class_level: int
    topic_id: int
    education_level: str = "high_school"
    subject_id: Optional[int] = None   # Filter questions by subject
    question_count: int = 10
    difficult: str


class AnswerSubmit(BaseModel):
    question_id: int
    answer: str
    topic: str = ""
    class_level: int = 9


@router.post("/start")
def start(body: MatchStart, user=Depends(student_required), request: Request = None):
    """
    Start a match session for the authenticated student.
    Returns a randomized list of questions (without correct answers).
    Prioritizes questions not answered within the cooldown window;
    falls back to all available questions if none remain outside cooldown.
    """
    with get_conn() as (conn, c):
        c.execute("SELECT id FROM students WHERE user_id = %s", (user["id"],))
        s = c.fetchone()
        if not s:
            raise HTTPException(status_code=404, detail="Student profile not found")
        student_id = s[0]

        # Clean up old match history beyond the retention window
        c.execute(
            "DELETE FROM match_history WHERE answered_at < NOW() - (%s * INTERVAL '1 day')",
            (HISTORY_KEEP_DAYS,)
        )
        conn.commit()

        c.execute(
            "SELECT name FROM topics WHERE id = %s AND class_level = %s AND education_level = %s",
            (body.topic_id, body.class_level, body.education_level)
        )
        topic = c.fetchone()
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        topic_name = topic[0]

        base_params = [body.class_level, topic_name, body.difficult, body.education_level]
        subject_filter = "AND subject_id = %s" if body.subject_id else ""
        if body.subject_id:
            base_params.append(body.subject_id)

        # Try to fetch questions not seen recently (respecting cooldown)
        cooldown_params = base_params + [student_id, COOLDOWN_DAYS]
        c.execute(f"""
            SELECT id, question_text, option_a, option_b, option_c, option_d, option_e
            FROM questions
            WHERE class_level = %s AND topic = %s AND difficult = %s AND education_level = %s
                {subject_filter}
                AND id NOT IN (
                    SELECT question_id FROM match_history
                    WHERE student_id = %s
                    AND answered_at > NOW() - (%s * INTERVAL '1 day')
                )
        """, cooldown_params)
        qs = c.fetchall()

        if not qs:
            # Cooldown exhausted — allow all questions for this topic
            c.execute(f"""
                SELECT id, question_text, option_a, option_b, option_c, option_d, option_e
                FROM questions
                WHERE class_level = %s AND topic = %s AND difficult = %s AND education_level = %s
                {subject_filter}
            """, base_params)
            qs = c.fetchall()

    if not qs:
        raise HTTPException(status_code=404, detail="No questions found for this topic")

    sel = random.sample(qs, min(len(qs), body.question_count))
    log_action(
        user, "match_started", "topic", body.topic_id,
        f"Topic: {topic_name}, Grade: {body.class_level}, Difficulty: {body.difficult}",
        request
    )
    return [
        {
            "id": q[0], "question": q[1],
            "options": {
                "a": q[2], "b": q[3], "c": q[4], "d": q[5],
                **( {"e": q[6]} if q[6] else {})
            }
        }
        for q in sel
    ]


@router.post("/submit")
def submit(body: AnswerSubmit, user=Depends(student_required)):
    """
    Submit an answer for a question.
    The student_id is always derived from the JWT token — never from the request body.
    Awards points, gold, and streak updates. Applies active boost multipliers.
    Grants a night bonus (+5 pts) for correct answers between midnight and 05:00.
    """
    with get_conn() as (conn, c):
        # Always resolve student from token to prevent ID spoofing
        c.execute("SELECT id FROM students WHERE user_id = %s", (user["id"],))
        s = c.fetchone()
        if not s:
            raise HTTPException(status_code=404, detail="Student profile not found")
        student_id = s[0]

        c.execute("SELECT correct_answer FROM questions WHERE id = %s", (body.question_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Question not found")

        is_correct = body.answer.strip().lower() == row[0].strip().lower()

        # Use INSERT ... ON CONFLICT DO NOTHING and check rowcount to detect duplicates.
        # Stats are only updated when a genuinely new answer is recorded, preventing
        # total_solved / total_correct inflation on repeated submissions of the same question.
        c.execute("""
            INSERT INTO match_history(student_id, question_id, is_correct)
            VALUES(%s, %s, %s) ON CONFLICT DO NOTHING
        """, (student_id, body.question_id, is_correct))
        already_answered = c.rowcount == 0

        if already_answered:
            # Duplicate submission — return the previous result without touching any counters.
            conn.commit()
            return {
                "correct": is_correct,
                "points_earned": 0,
                "streak_updated": False,
                "is_night_bonus": False,
                "message": "Already answered"
            }

        c.execute("""
            UPDATE students SET
                total_solved = total_solved + 1,
                total_correct = total_correct + %s,
                total_wrong = total_wrong + %s
            WHERE id = %s
        """, (1 if is_correct else 0, 0 if is_correct else 1, student_id))

        mult, pts, streak_up, night = 1, 0, False, False

        if is_correct:
            # Award the "First Step" badge on the very first correct answer
            award_badge(student_id, "First Step")

            tr = pytz.timezone("Europe/Istanbul")
            now = datetime.now(tr)
            night = 0 <= now.hour < 5  # Night bonus window

            # Apply the highest active boost multiplier if any
            c.execute("""
                SELECT multiplier FROM active_boosts
                WHERE student_id = %s AND expires_at > NOW()
                ORDER BY multiplier DESC LIMIT 1
            """, (student_id,))
            boost = c.fetchone()
            mult = boost[0] if boost else 1
            pts = (10 * mult) + (5 if night else 0)
            gold_earned = pts // 5

            # Increment streak only once per calendar day
            c.execute("SELECT last_active FROM students WHERE id = %s", (student_id,))
            la = c.fetchone()[0]
            today = now.date()
            last = None
            if la:
                if la.tzinfo is None:
                    la = la.replace(tzinfo=pytz.utc)
                last = la.astimezone(tr).date()

            if last is None or last < today:
                c.execute("""
                    UPDATE students
                    SET score = score + %s, gold = gold + %s,
                        streak = streak + 1, last_active = NOW()
                    WHERE id = %s
                """, (pts, gold_earned, student_id))
                streak_up = True
            else:
                c.execute("""
                    UPDATE students
                    SET score = score + %s, gold = gold + %s
                    WHERE id = %s
                """, (pts, gold_earned, student_id))

            # Check for milestone badges after updating score
            c.execute("SELECT score, gold FROM students WHERE id = %s", (student_id,))
            sd = c.fetchone()
            if sd:
                check_score_badges(student_id, sd[0], sd[1])

        conn.commit()

    # Update per-topic stats and overall success rate (outside the transaction for safety)
    if body.topic:
        update_topic_stats(student_id, body.topic, body.class_level, is_correct)
    update_success_rate(student_id)

    log_action(
        user, "question_answered", "question", body.question_id,
        f"{'correct' if is_correct else 'wrong'}, points={pts}, topic={body.topic}"
    )
    return {
        "correct": is_correct,
        "points_earned": pts,
        "streak_updated": streak_up,
        "is_night_bonus": night if is_correct else False,
        "message": "First session of the day! 🔥" if streak_up else "Well done!" if is_correct else "Wrong answer"
    }
