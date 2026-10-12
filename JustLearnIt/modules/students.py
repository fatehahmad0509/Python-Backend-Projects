"""
JustLearnIt - Students Module

Student-facing endpoints: profile, badges, homeworks,
notifications, and per-topic performance stats.
"""
import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.db import get_conn
from core.security import auth_required
from core.achievements import award_badge

router = APIRouter(prefix="/students")


def get_current_student(user_id: int):
    """Fetch core student fields for the given user_id. Returns None if not found."""
    with get_conn() as (conn, c):
        c.execute("""
            SELECT id, full_name, class_name, score, gold, streak, selected_badge
            FROM students
            WHERE user_id = %s
        """, (user_id,))
        return c.fetchone()


class BadgeSelectRequest(BaseModel):
    badge_name: str


@router.post("/select-badge")
def select_badge(body: BadgeSelectRequest, user=Depends(auth_required)):
    """Set the student's active display badge. The student must already own the badge."""
    with get_conn() as (conn, c):
        c.execute("SELECT id FROM students WHERE user_id = %s", (user["id"],))
        student = c.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        student_id = student[0]

        # Verify ownership before updating
        c.execute(
            "SELECT 1 FROM student_badges WHERE student_id = %s AND badge_name = %s",
            (student_id, body.badge_name)
        )
        if not c.fetchone():
            raise HTTPException(status_code=400, detail="You do not own this badge")

        c.execute("UPDATE students SET selected_badge = %s WHERE id = %s", (body.badge_name, student_id))
        conn.commit()
    return {"status": "ok"}


@router.get("/me")
def get_me(user=Depends(auth_required)):
    """
    Return the authenticated student's full profile and badge list.
    Also awards the 'School Legend' badge if the student is the top scorer in their school.
    """
    with get_conn() as (conn, c):
        c.execute("""
            SELECT id, full_name, class_name, score, gold, streak, selected_badge,
                   total_correct, total_wrong, success_percentage, class_level, education_level
            FROM students
            WHERE user_id = %s
        """, (user["id"],))
        student = c.fetchone()

        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")

        student_id = student[0]
        student_data = {
            "id": student[0],
            "student_id": student[0],
            "full_name": student[1],
            "class_name": student[2],
            "score": student[3],
            "gold": student[4],
            "streak": student[5],
            "selected_badge": student[6],
            "level": max(1, (student[3] or 0) // 500 + 1),
            "total_correct": student[7] or 0,
            "total_wrong": student[8] or 0,
            "success_percentage": float(student[9] or 0),
            "class_level": student[10] or 9,
            "education_level": student[11] or "high_school",
        }

        c.execute("SELECT badge_name FROM student_badges WHERE student_id = %s", (student_id,))
        badges = [row[0] for row in c.fetchall()]

        # Award 'School Legend' only to the top scorer within the student's own school
        school_id = user.get("school_id") if hasattr(user, "get") else None
        if school_id:
            c.execute("SELECT id FROM students WHERE school_id=%s ORDER BY score DESC LIMIT 1", (school_id,))
        else:
            c.execute("SELECT id FROM students ORDER BY score DESC LIMIT 1")
        top_id = c.fetchone()
        if top_id and top_id[0] == student_id:
            if "School Legend" not in badges:
                award_badge(student_id, "School Legend")
                badges.append("School Legend")

        return {"student": student_data, "badges": badges}


@router.get("/homeworks")
def my_homeworks(user=Depends(auth_required)):
    """Return all homework assignments for the authenticated student, newest first."""
    student = get_current_student(user["id"])
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    with get_conn() as (conn, c):
        c.execute("""
            SELECT id, title, description, due_date, is_completed, created_at
            FROM homeworks
            WHERE student_id = %s
            ORDER BY created_at DESC
        """, (student[0],))
        rows = c.fetchall()

    return [
        {
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "due_date": r[3].isoformat() if r[3] else None,
            "is_completed": r[4],
            "created_at": r[5].isoformat() if r[5] else None,
        }
        for r in rows
    ]


@router.get("/notifications")
def my_notifications(user=Depends(auth_required)):
    """Return the latest 20 notifications for the student, along with the unread count."""
    student = get_current_student(user["id"])
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    with get_conn() as (conn, c):
        c.execute("""
            SELECT id, title, message, is_read, created_at, homework_id
            FROM notifications
            WHERE student_id = %s
            ORDER BY created_at DESC
            LIMIT 20
        """, (student[0],))
        rows = c.fetchall()

    return {
        "unread_count": sum(1 for row in rows if not row[3]),
        "items": [
            {
                "id": r[0],
                "title": r[1],
                "message": r[2],
                "is_read": r[3],
                "created_at": r[4].isoformat() if r[4] else None,
                "homework_id": r[5],
            }
            for r in rows
        ],
    }


@router.post("/notifications/read-all")
def read_all_notifications(user=Depends(auth_required)):
    """Mark all unread notifications as read for the authenticated student."""
    student = get_current_student(user["id"])
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    with get_conn() as (conn, c):
        c.execute("""
            UPDATE notifications
            SET is_read = TRUE
            WHERE student_id = %s AND is_read = FALSE
        """, (student[0],))
        conn.commit()

    return {"message": "All notifications marked as read"}


@router.get("/performance")
def my_performance(user=Depends(auth_required)):
    """
    Return per-topic accuracy with a colour-coded evaluation label.
    Also includes an overall summary across all topics.
    """
    student = get_current_student(user["id"])
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    student_id = student[0]
    with get_conn() as (conn, c):
        c.execute("""
            SELECT topic, class_level, total_solved, total_correct, total_wrong, last_solved_at
            FROM student_topic_stats
            WHERE student_id = %s
            ORDER BY class_level, topic
        """, (student_id,))
        rows = c.fetchall()

    topics = []
    overall_total = 0
    overall_correct = 0

    for r in rows:
        total = r[2] or 0
        correct = r[3] or 0
        wrong = r[4] or 0
        accuracy = round((correct / total * 100), 1) if total > 0 else 0
        overall_total += total
        overall_correct += correct

        # Assign a feedback label and colour based on accuracy thresholds
        if accuracy >= 90:
            evaluation = "Outstanding! Keep it up!"
            color = "green"
        elif accuracy >= 80:
            evaluation = "Great performance! Almost perfect!"
            color = "lightblue"
        elif accuracy >= 60:
            evaluation = "Decent effort, but you should practise more regularly."
            color = "yellow"
        else:
            evaluation = "Needs improvement — increase your study time immediately!"
            color = "red"

        topics.append({
            "topic_name": r[0],
            "class_level": r[1],
            "total_questions": total,
            "correct_answers": correct,
            "wrong_answers": wrong,
            "accuracy_percent": accuracy,
            "evaluation": evaluation,
            "color": color,
            "updated_at": r[5].isoformat() if r[5] else None,
        })

    overall_accuracy = round((overall_correct / overall_total * 100), 1) if overall_total > 0 else 0

    return {
        "topics": topics,
        "overall": {
            "total_questions": overall_total,
            "correct_answers": overall_correct,
            "wrong_answers": overall_total - overall_correct,
            "accuracy_percent": overall_accuracy,
        }
    }


@router.get("/topic-stats")
def my_topic_stats(user=Depends(auth_required)):
    """Return per-topic statistics sorted by number of questions solved (descending)."""
    student = get_current_student(user["id"])
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    student_id = student[0]
    with get_conn() as (conn, c):
        c.execute("""
            SELECT topic, class_level, total_correct, total_wrong, total_solved, last_solved_at
            FROM student_topic_stats
            WHERE student_id = %s
            ORDER BY total_solved DESC
        """, (student_id,))
        rows = c.fetchall()

    return [
        {
            "topic": r[0],
            "class_level": r[1],
            "total_correct": r[2] or 0,
            "total_wrong": r[3] or 0,
            "total_solved": r[4] or 0,
            "success_pct": round((r[2] or 0) / r[4] * 100, 1) if r[4] else 0,
            "last_solved_at": r[5].isoformat() if r[5] else None,
        }
        for r in rows
    ]


@router.get("/")
def all_students(
    page: int = 1,
    limit: int = 20,
    user=Depends(auth_required),
):
    """Return a paginated leaderboard of all students sorted by score descending."""
    offset = (page - 1) * limit
    with get_conn() as (conn, c):
        c.execute("""
            SELECT id, full_name, class_name, score, gold, streak, selected_badge
            FROM students
            ORDER BY score DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        data = c.fetchall()

    return [
        {
            "student_id": d[0],
            "full_name": d[1],
            "class_name": d[2],
            "score": d[3],
            "gold": d[4],
            "streak": d[5],
            "selected_badge": d[6],
            "level": max(1, (d[3] or 0) // 500 + 1),
        }
        for d in data
    ]


def check_streak_protection(student_id, cursor):
    """Return True if the student has an active Streak Freeze boost."""
    cursor.execute("""
        SELECT 1 FROM active_boosts
        WHERE student_id = %s AND item_name = 'Streak Freeze' AND expires_at > NOW()
    """, (student_id,))
    return cursor.fetchone() is not None
