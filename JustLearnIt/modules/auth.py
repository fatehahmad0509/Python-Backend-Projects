"""
JustLearnIt - Authentication Module

Handles user login, JWT token issuance, and student profile
retrieval with streak validation on login.
"""
import re
from datetime import datetime
import pytz
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from core.db import get_conn
from core.security import create_token, hash_password
from core.logs import log_action

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(body: LoginRequest, request: Request = None):
    """
    Authenticate a user and return a JWT token along with role and student info.
    Raises 401 for invalid credentials and 403 if the account or school is blocked.
    """
    u, p = body.username.strip(), body.password.strip()
    if not u or not p:
        raise HTTPException(400, "Username and password are required")

    with get_conn() as (conn, c):
        c.execute("""SELECT u.id,u.username,u.role,u.school_id,u.is_blocked,
            s.name,s.is_blocked,s.is_active FROM users u
            LEFT JOIN schools s ON s.id=u.school_id
            WHERE u.username=%s AND u.password=%s""", (u, hash_password(p)))
        row = c.fetchone()

    if not row:
        raise HTTPException(401, "Invalid username or password")

    uid, uname, role, school_id, blocked, school_name, s_blocked, s_active = row

    if blocked:
        raise HTTPException(403, "Your account has been blocked. Please contact your school.")
    if school_id and (s_blocked or not s_active):
        raise HTTPException(403, "Your school's access has been suspended.")

    token = create_token({"id": uid, "username": uname, "role": role, "school_id": school_id})
    student = _get_student(uid) if role == "student" else None

    log_action({"id": uid, "username": uname, "role": role}, "login", detail=f"role={role}", request=request)
    return {"token": token, "role": role, "school_name": school_name, "student": student}


def _get_student(user_id):
    """
    Fetch the student profile for the given user_id.
    Resets the streak to zero if the student missed a day and has no active Streak Freeze boost.
    """
    tr = pytz.timezone("Europe/Istanbul")
    now = datetime.now(tr)
    with get_conn() as (conn, c):
        c.execute("""SELECT id,full_name,class_name,class_level,education_level,
            score,gold,streak,last_active,total_correct,total_wrong,total_solved,success_percentage
            FROM students WHERE user_id=%s""", (user_id,))
        s = c.fetchone()
        if not s:
            return None

        sid, fname, cname, clvl, edu, score, gold, streak, last_a, tc, tw, ts, sp = s

        # Reset streak if the student missed a day and has no active streak protection
        if last_a:
            if last_a.tzinfo is None:
                last_a = last_a.replace(tzinfo=pytz.utc)
            if (now.date() - last_a.astimezone(tr).date()).days >= 2:
                c.execute(
                    "SELECT 1 FROM active_boosts WHERE student_id=%s AND item_name='Streak Freeze' AND expires_at>NOW()",
                    (sid,)
                )
                if not c.fetchone():
                    c.execute("UPDATE students SET streak=0 WHERE id=%s", (sid,))
                    conn.commit()
                    streak = 0

        # Derive class_level from class_name if not explicitly stored
        if not clvl and cname:
            m = re.search(r'\d+', cname or "")
            clvl = int(m.group()) if m else 9

        return {
            "student_id": sid, "full_name": fname, "class_name": cname,
            "class_level": clvl or 9, "education_level": edu or "high_school",
            "score": score or 0, "gold": gold or 0, "streak": streak or 0,
            "level": max(1, (score or 0) // 500 + 1),
            "total_correct": tc or 0, "total_wrong": tw or 0,
            "total_solved": ts or 0, "success_percentage": float(sp or 0)
        }
