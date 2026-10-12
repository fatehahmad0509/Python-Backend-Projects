"""
JustLearnIt - Teacher Panel

Endpoints for teachers and admins to view student data, manage homeworks,
and browse subjects and topics. School-scoped filtering is applied automatically
for teachers; admins have unrestricted access.
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from core.db import get_conn
from core.security import teacher_or_admin, get_school_filter
from core.logs import log_action

router = APIRouter(prefix="/teacher", tags=["Teacher"])


class HomeworkCreate(BaseModel):
    student_id: int
    title: str
    description: str
    due_date: Optional[date] = None


class HomeworkUpdate(BaseModel):
    is_completed: bool


def _sf(user):
    """Shorthand helper to retrieve the school filter for the current user."""
    return get_school_filter(user)


@router.get("/dashboard")
def dashboard(user=Depends(teacher_or_admin)):
    """Return a quick summary: total students, average score, and average success rate."""
    sf = _sf(user)
    with get_conn() as (conn, c):
        if sf:
            c.execute(
                "SELECT COUNT(*),AVG(score),AVG(success_percentage) FROM students WHERE school_id=%s",
                (sf,)
            )
        else:
            c.execute("SELECT COUNT(*),AVG(score),AVG(success_percentage) FROM students")
        r = c.fetchone()
    return {"total_students": r[0], "avg_score": float(r[1] or 0), "avg_success_pct": float(r[2] or 0)}


@router.get("/students")
def list_students(user=Depends(teacher_or_admin)):
    """Return all students (scoped to the teacher's school) sorted by score descending."""
    sf = _sf(user)
    with get_conn() as (conn, c):
        if sf:
            c.execute("""
                SELECT s.id,s.user_id,s.full_name,s.class_name,s.class_level,s.education_level,
                       s.score,s.gold,s.streak,u.username,s.total_correct,s.total_wrong,
                       s.total_solved,s.success_percentage
                FROM students s JOIN users u ON u.id=s.user_id
                WHERE s.school_id=%s ORDER BY s.score DESC
            """, (sf,))
        else:
            c.execute("""
                SELECT s.id,s.user_id,s.full_name,s.class_name,s.class_level,s.education_level,
                       s.score,s.gold,s.streak,u.username,s.total_correct,s.total_wrong,
                       s.total_solved,s.success_percentage
                FROM students s JOIN users u ON u.id=s.user_id ORDER BY s.score DESC
            """)
        rows = c.fetchall()
    return [
        {
            "student_id": r[0], "user_id": r[1], "full_name": r[2], "class_name": r[3],
            "class_level": r[4], "education_level": r[5], "score": r[6], "gold": r[7],
            "streak": r[8], "username": r[9], "total_correct": r[10], "total_wrong": r[11],
            "total_solved": r[12], "success_pct": float(r[13] or 0),
            "level": max(1, (r[6] or 0) // 500 + 1)
        }
        for r in rows
    ]


@router.get("/students/{sid}/report")
def student_report(sid: int, user=Depends(teacher_or_admin)):
    """Return a detailed report for a single student including topic stats and earned badges."""
    sf = _sf(user)
    with get_conn() as (conn, c):
        q = """SELECT s.id,s.full_name,s.class_name,s.class_level,s.education_level,
                      s.score,s.gold,s.streak,s.total_correct,s.total_wrong,
                      s.total_solved,s.success_percentage,s.last_active
               FROM students s WHERE s.id=%s"""
        params = [sid]
        if sf:
            q += " AND s.school_id=%s"
            params.append(sf)
        c.execute(q, params)
        s = c.fetchone()
        if not s:
            raise HTTPException(404, "Student not found")

        c.execute("""
            SELECT topic, class_level, total_correct, total_wrong, total_solved,
                   CASE WHEN total_solved>0
                        THEN ROUND(total_correct::NUMERIC/total_solved*100,1) ELSE 0 END
            FROM student_topic_stats WHERE student_id=%s ORDER BY total_solved DESC
        """, (sid,))
        topics = [
            {"topic": r[0], "class_level": r[1], "correct": r[2],
             "wrong": r[3], "solved": r[4], "success_pct": float(r[5])}
            for r in c.fetchall()
        ]

        c.execute("SELECT badge_name,awarded_at FROM student_badges WHERE student_id=%s", (sid,))
        badges = [{"name": r[0], "awarded_at": r[1].isoformat() if r[1] else None} for r in c.fetchall()]

    return {
        "student_id": s[0], "full_name": s[1], "class_name": s[2], "class_level": s[3],
        "education_level": s[4], "score": s[5], "gold": s[6], "streak": s[7],
        "total_correct": s[8], "total_wrong": s[9], "total_solved": s[10],
        "success_percentage": float(s[11] or 0),
        "last_active": s[12].isoformat() if s[12] else None,
        "level": max(1, (s[5] or 0) // 500 + 1),
        "topic_stats": topics, "badges": badges
    }


@router.get("/classes")
def classes(user=Depends(teacher_or_admin)):
    """Return a sorted list of distinct class names within the teacher's school."""
    sf = _sf(user)
    with get_conn() as (conn, c):
        if sf:
            c.execute(
                "SELECT DISTINCT class_name FROM students WHERE school_id=%s ORDER BY class_name",
                (sf,)
            )
        else:
            c.execute("SELECT DISTINCT class_name FROM students ORDER BY class_name")
        return [d[0] for d in c.fetchall()]


@router.get("/homeworks")
def list_hw(user=Depends(teacher_or_admin)):
    """Return all homework assignments (scoped to the teacher's school), newest first."""
    sf = _sf(user)
    with get_conn() as (conn, c):
        if sf:
            c.execute("""
                SELECT h.id,h.student_id,s.full_name,h.title,h.description,
                       h.due_date,h.created_at,h.is_completed
                FROM homeworks h JOIN students s ON s.id=h.student_id
                WHERE s.school_id=%s ORDER BY h.created_at DESC
            """, (sf,))
        else:
            c.execute("""
                SELECT h.id,h.student_id,s.full_name,h.title,h.description,
                       h.due_date,h.created_at,h.is_completed
                FROM homeworks h JOIN students s ON s.id=h.student_id
                ORDER BY h.created_at DESC
            """)
        rows = c.fetchall()
    return [
        {
            "id": r[0], "student_id": r[1], "student_name": r[2],
            "title": r[3], "description": r[4],
            "due_date": r[5].isoformat() if r[5] else None,
            "created_at": r[6].isoformat() if r[6] else None,
            "is_completed": r[7] if r[7] is not None else False
        }
        for r in rows
    ]


@router.post("/homeworks")
def add_hw(body: HomeworkCreate, user=Depends(teacher_or_admin), request: Request = None):
    """
    Assign a new homework to a student and create a corresponding notification.
    Both title and description are required.
    """
    if not body.title.strip() or not body.description.strip():
        raise HTTPException(400, "Title and description are required")

    sf = _sf(user)
    with get_conn() as (conn, c):
        q = "SELECT full_name FROM students WHERE id=%s"
        params = [body.student_id]
        if sf:
            q += " AND school_id=%s"
            params.append(sf)
        c.execute(q, params)
        s = c.fetchone()
        if not s:
            raise HTTPException(404, "Student not found")

        c.execute("""INSERT INTO homeworks(student_id,title,description,due_date,created_by)
                     VALUES(%s,%s,%s,%s,%s) RETURNING id""",
                  (body.student_id, body.title.strip(), body.description.strip(),
                   body.due_date, user["id"]))
        hw_id = c.fetchone()[0]

        due = body.due_date.strftime("%d.%m.%Y") if body.due_date else "Not specified"
        c.execute(
            "INSERT INTO notifications(student_id,title,message,homework_id) VALUES(%s,%s,%s,%s)",
            (body.student_id, "New homework assigned",
             f"'{body.title.strip()}' has been assigned to you. Due: {due}", hw_id)
        )
        conn.commit()

    log_action(user, "homework_added", "homework", hw_id,
               f"Student: {s[0]}, Title: {body.title.strip()}", request)
    return {"message": f"Homework created for {s[0]}", "homework_id": hw_id}


@router.patch("/homeworks/{hw_id}/complete")
def update_hw(hw_id: int, body: HomeworkUpdate, user=Depends(teacher_or_admin)):
    """Mark a homework as completed or incomplete."""
    with get_conn() as (conn, c):
        c.execute("SELECT id FROM homeworks WHERE id=%s", (hw_id,))
        if not c.fetchone():
            raise HTTPException(404, "Homework not found")
        c.execute("UPDATE homeworks SET is_completed=%s WHERE id=%s", (body.is_completed, hw_id))
        conn.commit()
    log_action(
        user,
        "homework_completed" if body.is_completed else "homework_uncompleted",
        "homework", hw_id
    )
    return {"message": "Homework updated"}


@router.get("/subjects")
def get_subjects(
    class_level: int = None,
    education_level: str = None,
    user=Depends(teacher_or_admin)
):
    """Return subjects with their topic counts. Supports optional filtering by class and education level."""
    q = """SELECT s.id, s.name, s.education_level, s.class_level, s.display_order,
                  COUNT(t.id) as topic_count
           FROM subjects s LEFT JOIN topics t ON t.subject_id = s.id
           WHERE 1=1"""
    params = []
    if class_level:
        q += " AND s.class_level=%s"
        params.append(class_level)
    if education_level:
        q += " AND s.education_level=%s"
        params.append(education_level)
    q += " GROUP BY s.id ORDER BY s.education_level, s.class_level, s.display_order, s.name"
    with get_conn() as (conn, c):
        c.execute(q, params)
        rows = c.fetchall()
    return [
        {"id": r[0], "name": r[1], "education_level": r[2],
         "class_level": r[3], "display_order": r[4], "topic_count": r[5]}
        for r in rows
    ]


@router.get("/topics")
def topics(
    class_level: int = None,
    education_level: str = None,
    subject_id: int = None,
    user=Depends(teacher_or_admin)
):
    """Return topics with their subject name. Supports filtering by class, education level, and subject."""
    q = """SELECT t.id, t.name, t.class_level, t.education_level, t.display_order,
                  s.name as subject_name, t.subject_id
           FROM topics t LEFT JOIN subjects s ON s.id = t.subject_id
           WHERE 1=1"""
    params = []
    if class_level:
        q += " AND t.class_level=%s"
        params.append(class_level)
    if education_level:
        q += " AND t.education_level=%s"
        params.append(education_level)
    if subject_id:
        q += " AND t.subject_id=%s"
        params.append(subject_id)
    q += " ORDER BY t.education_level, t.class_level, t.display_order, t.name"
    with get_conn() as (conn, c):
        c.execute(q, params)
        rows = c.fetchall()
    return [
        {"id": r[0], "name": r[1], "class_level": r[2], "education_level": r[3],
         "display_order": r[4], "subject": r[5], "subject_id": r[6]}
        for r in rows
    ]
