"""
JustLearnIt - Admin Panel

Full platform management: schools, users, students, teachers,
subjects, topics, questions, statistics, and audit logs.
"""
from typing import Optional
from datetime import datetime
import pytz
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel
from core.db import get_conn
from core.security import admin_required, hash_password
from core.logs import log_action

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Pydantic Request Models ────────────────────────────────────

class SchoolCreate(BaseModel):
    name: str
    city: Optional[str] = None
    district: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class SchoolUpdate(BaseModel):
    is_blocked: Optional[bool] = None
    is_active: Optional[bool] = None

class StudentCreate(BaseModel):
    full_name: str; username: str; password: str; class_name: str
    class_level: int = 9; education_level: str = "high_school"; school_id: int

class TeacherCreate(BaseModel):
    full_name: str; username: str; password: str; school_id: int

class AdminCreate(BaseModel):
    username: str; password: str

class UserBlock(BaseModel):
    is_blocked: bool

class SubjectCreate(BaseModel):
    name: str
    education_level: str = "high_school"
    class_level: int
    display_order: int = 0

class TopicCreate(BaseModel):
    name: str
    class_level: int
    education_level: str = "high_school"
    subject_id: int          # Required — topics must belong to a subject
    display_order: int = 0

class QuestionCreate(BaseModel):
    question_text: str; option_a: str; option_b: str
    option_c: str; option_d: str; option_e: Optional[str] = None
    correct_answer: str; class_level: int
    education_level: str = "high_school"
    topic_id: int
    subject_id: int          # Required — questions must belong to a subject
    difficult: str = "easy"


# ── Admin Account Management ──────────────────────────────────

@router.post("/create-admin")
def create_admin(body: AdminCreate, user=Depends(admin_required)):
    """Create a new admin account. Username and password are required."""
    if not body.username.strip() or not body.password.strip():
        raise HTTPException(400, "Username and password are required")
    with get_conn() as (conn, c):
        try:
            c.execute(
                "INSERT INTO users(username,password,role) VALUES(%s,%s,'admin') RETURNING id",
                (body.username.strip(), hash_password(body.password.strip()))
            )
            uid = c.fetchone()[0]
            conn.commit()
        except Exception:
            conn.rollback()
            raise HTTPException(400, "This username is already taken")
    log_action(user, "admin_created", "user", uid, f"New admin: {body.username.strip()}")
    return {"message": "Admin account created", "user_id": uid}


# ── School Management ─────────────────────────────────────────

@router.get("/schools")
def list_schools(user=Depends(admin_required)):
    """Return all schools with their student counts."""
    with get_conn() as (conn, c):
        c.execute("""
            SELECT s.id,s.name,s.city,s.district,s.phone,s.email,
                   s.is_active,s.is_blocked,s.created_at,COUNT(st.id)
            FROM schools s LEFT JOIN students st ON st.school_id=s.id
            GROUP BY s.id ORDER BY s.name
        """)
        rows = c.fetchall()
    return [
        {
            "id": r[0], "name": r[1], "city": r[2], "district": r[3],
            "phone": r[4], "email": r[5], "is_active": r[6], "is_blocked": r[7],
            "created_at": r[8].isoformat() if r[8] else None, "student_count": r[9]
        }
        for r in rows
    ]

@router.post("/schools")
def create_school(body: SchoolCreate, user=Depends(admin_required)):
    """Create a new school. Name must be unique."""
    if not body.name.strip():
        raise HTTPException(400, "School name is required")
    with get_conn() as (conn, c):
        try:
            c.execute(
                "INSERT INTO schools(name,city,district,phone,email) VALUES(%s,%s,%s,%s,%s) RETURNING id",
                (body.name.strip(), body.city, body.district, body.phone, body.email)
            )
            sid = c.fetchone()[0]
            conn.commit()
        except Exception:
            conn.rollback()
            raise HTTPException(400, "A school with this name already exists")
    log_action(user, "school_added", "school", sid, f"School: {body.name.strip()}")
    return {"message": "School added", "school_id": sid}

@router.patch("/schools/{sid}")
def update_school(sid: int, body: SchoolUpdate, user=Depends(admin_required)):
    """Toggle a school's blocked or active status."""
    with get_conn() as (conn, c):
        if body.is_blocked is not None:
            c.execute("UPDATE schools SET is_blocked=%s WHERE id=%s", (body.is_blocked, sid))
        if body.is_active is not None:
            c.execute("UPDATE schools SET is_active=%s WHERE id=%s", (body.is_active, sid))
        conn.commit()
    log_action(user, "school_updated", "school", sid, f"blocked={body.is_blocked}, active={body.is_active}")
    return {"message": "School updated"}

@router.delete("/schools/{sid}")
def delete_school(sid: int, user=Depends(admin_required)):
    """Permanently delete a school record."""
    with get_conn() as (conn, c):
        c.execute("SELECT id FROM schools WHERE id=%s", (sid,))
        if not c.fetchone():
            raise HTTPException(404, "School not found")
        c.execute("DELETE FROM schools WHERE id=%s", (sid,))
        conn.commit()
    log_action(user, "school_deleted", "school", sid)
    return {"message": "School deleted"}


# ── User Management ───────────────────────────────────────────

@router.get("/users")
def list_users(user=Depends(admin_required)):
    """Return all users with their role, school, and block status."""
    with get_conn() as (conn, c):
        c.execute("""
            SELECT u.id,u.username,u.role,u.is_blocked,u.created_at,s.name
            FROM users u LEFT JOIN schools s ON s.id=u.school_id
            ORDER BY u.created_at DESC
        """)
        rows = c.fetchall()
    return [
        {
            "id": r[0], "username": r[1], "role": r[2], "is_blocked": r[3],
            "created_at": r[4].isoformat() if r[4] else None, "school": r[5]
        }
        for r in rows
    ]

@router.patch("/users/{uid}/block")
def block_user(uid: int, body: UserBlock, user=Depends(admin_required)):
    """Block or unblock a user account."""
    with get_conn() as (conn, c):
        c.execute("UPDATE users SET is_blocked=%s WHERE id=%s", (body.is_blocked, uid))
        conn.commit()
    log_action(
        user,
        "user_blocked" if body.is_blocked else "user_unblocked",
        "user", uid
    )
    return {"message": "User updated"}


# ── Student & Teacher Management ──────────────────────────────

@router.post("/students")
def add_student(body: StudentCreate, user=Depends(admin_required)):
    """Create a student user account and the linked student profile."""
    if not all([body.full_name.strip(), body.username.strip(), body.password.strip(), body.class_name.strip()]):
        raise HTTPException(400, "All fields are required")
    if body.education_level not in ("primary", "middle", "high_school"):
        raise HTTPException(400, "Invalid education level")
    with get_conn() as (conn, c):
        c.execute("SELECT id FROM schools WHERE id=%s", (body.school_id,))
        if not c.fetchone():
            raise HTTPException(404, "School not found")
        try:
            c.execute(
                "INSERT INTO users(username,password,role,school_id) VALUES(%s,%s,'student',%s) RETURNING id",
                (body.username.strip(), hash_password(body.password.strip()), body.school_id)
            )
            uid = c.fetchone()[0]
            c.execute("""INSERT INTO students(user_id,school_id,full_name,class_name,class_level,education_level)
                         VALUES(%s,%s,%s,%s,%s,%s) RETURNING id""",
                      (uid, body.school_id, body.full_name.strip(), body.class_name.strip(),
                       body.class_level, body.education_level))
            student_id = c.fetchone()[0]
            conn.commit()
        except Exception:
            conn.rollback()
            raise HTTPException(400, "This username is already taken")
    log_action(user, "student_added", "student", student_id, f"{body.full_name.strip()} / {body.username.strip()}")
    return {"message": "Student added", "student_id": student_id}

@router.post("/teachers")
def add_teacher(body: TeacherCreate, user=Depends(admin_required)):
    """Create a teacher user account."""
    if not all([body.full_name.strip(), body.username.strip(), body.password.strip()]):
        raise HTTPException(400, "All fields are required")
    with get_conn() as (conn, c):
        c.execute("SELECT id FROM schools WHERE id=%s", (body.school_id,))
        if not c.fetchone():
            raise HTTPException(404, "School not found")
        try:
            c.execute(
                "INSERT INTO users(username,password,role,school_id) VALUES(%s,%s,'teacher',%s) RETURNING id",
                (body.username.strip(), hash_password(body.password.strip()), body.school_id)
            )
            uid = c.fetchone()[0]
            conn.commit()
        except Exception:
            conn.rollback()
            raise HTTPException(400, "This username is already taken")
    return {"message": "Teacher added", "user_id": uid}

@router.delete("/students/{sid}")
def delete_student(sid: int, user=Depends(admin_required)):
    """Delete a student and their linked user account."""
    with get_conn() as (conn, c):
        c.execute("SELECT user_id FROM students WHERE id=%s", (sid,))
        row = c.fetchone()
        if not row:
            raise HTTPException(404, "Student not found")
        c.execute("DELETE FROM students WHERE id=%s", (sid,))
        c.execute("DELETE FROM users WHERE id=%s", (row[0],))
        conn.commit()
    return {"message": "Student deleted"}


# ── Subject Management ────────────────────────────────────────

@router.get("/subjects")
def list_subjects(
    class_level: int = None,
    education_level: str = None,
    user=Depends(admin_required)
):
    """List all subjects with topic counts. Supports optional filtering."""
    q = """SELECT s.id, s.name, s.education_level, s.class_level, s.display_order,
                  COUNT(t.id) as topic_count
           FROM subjects s LEFT JOIN topics t ON t.subject_id = s.id
           WHERE 1=1"""
    params = []
    if class_level:
        q += " AND s.class_level = %s"
        params.append(class_level)
    if education_level:
        q += " AND s.education_level = %s"
        params.append(education_level)
    q += " GROUP BY s.id ORDER BY s.education_level, s.class_level, s.display_order, s.name"
    with get_conn() as (conn, c):
        c.execute(q, params)
        rows = c.fetchall()
    return [
        {"id": r[0], "name": r[1], "education_level": r[2], "class_level": r[3],
         "display_order": r[4], "topic_count": r[5]}
        for r in rows
    ]

@router.post("/subjects")
def add_subject(body: SubjectCreate, user=Depends(admin_required)):
    """Add a new subject. Name must be unique within the same education level and class."""
    if not body.name.strip():
        raise HTTPException(400, "Subject name is required")
    if body.education_level not in ("primary", "middle", "high_school"):
        raise HTTPException(400, "Invalid education level")
    with get_conn() as (conn, c):
        try:
            c.execute("""INSERT INTO subjects(name,education_level,class_level,display_order)
                         VALUES(%s,%s,%s,%s) RETURNING id""",
                      (body.name.strip(), body.education_level, body.class_level, body.display_order))
            sid = c.fetchone()[0]
            conn.commit()
        except Exception:
            conn.rollback()
            raise HTTPException(400, "This subject already exists")
    log_action(user, "subject_added", "subject", sid,
               f"{body.name.strip()} / {body.education_level} / Grade {body.class_level}")
    return {"message": "Subject added", "subject_id": sid}

@router.delete("/subjects/{sid}")
def delete_subject(sid: int, user=Depends(admin_required)):
    """Delete a subject by ID."""
    with get_conn() as (conn, c):
        c.execute("DELETE FROM subjects WHERE id=%s RETURNING id", (sid,))
        if not c.fetchone():
            raise HTTPException(404, "Subject not found")
        conn.commit()
    log_action(user, "subject_deleted", "subject", sid)
    return {"message": "Subject deleted"}


# ── Topic Management ──────────────────────────────────────────

@router.get("/topics")
def list_topics(
    class_level: int = None, education_level: str = None,
    subject_id: int = None, user=Depends(admin_required)
):
    """List all topics with their parent subject name. Supports optional filtering."""
    q = """SELECT t.id, t.name, t.class_level, t.education_level,
                  t.display_order, s.name as subject_name, t.subject_id
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

@router.post("/topics")
def add_topic(body: TopicCreate, user=Depends(admin_required)):
    """Add a new topic under an existing subject."""
    if not body.name.strip():
        raise HTTPException(400, "Topic name is required")
    if body.education_level not in ("primary", "middle", "high_school"):
        raise HTTPException(400, "Invalid education level")
    with get_conn() as (conn, c):
        # Verify the parent subject exists
        c.execute("SELECT name FROM subjects WHERE id=%s", (body.subject_id,))
        subj = c.fetchone()
        if not subj:
            raise HTTPException(404, "Subject not found")
        try:
            c.execute("""INSERT INTO topics(name,class_level,education_level,subject_id,subject,display_order)
                         VALUES(%s,%s,%s,%s,%s,%s) RETURNING id""",
                      (body.name.strip(), body.class_level, body.education_level,
                       body.subject_id, subj[0], body.display_order))
            tid = c.fetchone()[0]
            conn.commit()
        except Exception:
            conn.rollback()
            raise HTTPException(400, "This topic already exists")
    log_action(user, "topic_added", "topic", tid, f"{body.name.strip()} / Grade {body.class_level}")
    return {"message": "Topic added", "topic_id": tid}

@router.delete("/topics/{tid}")
def del_topic(tid: int, user=Depends(admin_required)):
    """Delete a topic by ID."""
    with get_conn() as (conn, c):
        c.execute("DELETE FROM topics WHERE id=%s RETURNING id", (tid,))
        if not c.fetchone():
            raise HTTPException(404, "Topic not found")
        conn.commit()
    log_action(user, "topic_deleted", "topic", tid)
    return {"message": "Topic deleted"}


# ── Question Management ───────────────────────────────────────

@router.get("/questions")
def list_q(
    class_level: int = None, education_level: str = None,
    subject_id: int = None, topic_id: int = None,
    user=Depends(admin_required)
):
    """List questions with their subject name. Supports filtering by class, level, subject, or topic."""
    q = """SELECT q.id, q.question_text, q.class_level, q.education_level,
                  q.topic, q.difficult, s.name as subject_name
           FROM questions q LEFT JOIN subjects s ON s.id = q.subject_id
           WHERE 1=1"""
    params = []
    if class_level:
        q += " AND q.class_level=%s"
        params.append(class_level)
    if education_level:
        q += " AND q.education_level=%s"
        params.append(education_level)
    if subject_id:
        q += " AND q.subject_id=%s"
        params.append(subject_id)
    if topic_id:
        q += " AND q.topic=(SELECT name FROM topics WHERE id=%s)"
        params.append(topic_id)
    q += " ORDER BY q.education_level, q.class_level, q.topic"
    with get_conn() as (conn, c):
        c.execute(q, params)
        rows = c.fetchall()
    return [
        {"id": r[0], "question": r[1], "class_level": r[2], "education_level": r[3],
         "topic": r[4], "difficult": r[5], "subject": r[6]}
        for r in rows
    ]

@router.post("/questions")
def add_q(body: QuestionCreate, user=Depends(admin_required)):
    """
    Add a new question. Validates education level, correct answer (a-e),
    difficulty level, and ensures the topic belongs to the specified subject.
    """
    if body.education_level not in ("primary", "middle", "high_school"):
        raise HTTPException(400, "Invalid education level")
    if body.correct_answer.lower() not in ("a", "b", "c", "d", "e"):
        raise HTTPException(400, "Correct answer must be one of: a, b, c, d, e")
    if body.difficult not in ("easy", "medium", "hard"):
        raise HTTPException(400, "Invalid difficulty level")
    with get_conn() as (conn, c):
        # Verify the subject exists
        c.execute("SELECT name FROM subjects WHERE id=%s", (body.subject_id,))
        subj = c.fetchone()
        if not subj:
            raise HTTPException(404, "Subject not found")

        # Verify the topic exists and belongs to the given subject
        c.execute("""SELECT id, name FROM topics
                     WHERE id=%s AND class_level=%s AND education_level=%s AND subject_id=%s""",
                  (body.topic_id, body.class_level, body.education_level, body.subject_id))
        topic = c.fetchone()
        if not topic:
            raise HTTPException(400, "Invalid topic or topic does not match the specified subject")

        c.execute("""
            INSERT INTO questions(
                question_text,option_a,option_b,option_c,option_d,option_e,
                correct_answer,class_level,education_level,topic,
                subject_id,subject,difficult,created_by)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (body.question_text, body.option_a, body.option_b, body.option_c, body.option_d,
              body.option_e, body.correct_answer.lower(), body.class_level, body.education_level,
              topic[1], body.subject_id, subj[0], body.difficult, user["id"]))
        qid = c.fetchone()[0]
        conn.commit()
    log_action(user, "question_added", "question", qid, f"Topic: {topic[1]}, Grade: {body.class_level}")
    return {"message": "Question added", "question_id": qid}

@router.delete("/questions/{qid}")
def del_q(qid: int, user=Depends(admin_required)):
    """Delete a question by ID."""
    with get_conn() as (conn, c):
        c.execute("DELETE FROM questions WHERE id=%s RETURNING id", (qid,))
        if not c.fetchone():
            raise HTTPException(404, "Question not found")
        conn.commit()
    log_action(user, "question_deleted", "question", qid)
    return {"message": "Question deleted"}


# ── Platform Statistics ───────────────────────────────────────

@router.get("/stats")
def stats(user=Depends(admin_required)):
    """Return high-level platform statistics: schools, students, teachers, questions, and avg success."""
    with get_conn() as (conn, c):
        c.execute("SELECT COUNT(*) FROM schools WHERE is_active=TRUE")
        schools = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM students")
        students = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM users WHERE role='teacher'")
        teachers = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM questions")
        questions = c.fetchone()[0]
        c.execute("SELECT AVG(success_percentage) FROM students WHERE total_solved>0")
        avg = c.fetchone()[0]
    return {
        "total_schools": schools, "total_students": students,
        "total_teachers": teachers, "total_questions": questions,
        "avg_success_pct": float(avg or 0)
    }


# ── Audit Logs ────────────────────────────────────────────────

@router.get("/logs")
def get_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    action: str = Query(None),
    username: str = Query(None),
    user=Depends(admin_required)
):
    """
    Return paginated audit logs. Supports filtering by action string and username.
    Results are ordered by most recent first.
    """
    offset = (page - 1) * limit
    q = "SELECT id,user_id,username,role,action,target_type,target_id,detail,created_at FROM system_logs WHERE 1=1"
    params = []
    if action:
        q += " AND action=%s"
        params.append(action)
    if username:
        q += " AND username ILIKE %s"
        params.append(f"%{username}%")

    # Build a matching count query for pagination metadata
    count_q = "SELECT COUNT(*) FROM system_logs WHERE 1=1"
    count_p = []
    if action:
        count_q += " AND action=%s"
        count_p.append(action)
    if username:
        count_q += " AND username ILIKE %s"
        count_p.append(f"%{username}%")

    q += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params += [limit, offset]

    with get_conn() as (conn, c):
        c.execute(count_q, count_p)
        total = c.fetchone()[0]
        c.execute(q, params)
        rows = c.fetchall()

    return {
        "total": total, "page": page, "limit": limit,
        "logs": [
            {
                "id": r[0], "user_id": r[1], "username": r[2], "role": r[3],
                "action": r[4], "target_type": r[5], "target_id": r[6],
                "detail": r[7],
                "created_at": r[8].isoformat() if r[8] else None
            }
            for r in rows
        ]
    }
