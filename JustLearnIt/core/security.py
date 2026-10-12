"""
JustLearnIt - Security & Authentication

JWT token creation/verification, password hashing,
and FastAPI dependency functions for role-based access control.
"""
import hashlib, os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Header
from jose import JWTError, jwt

SECRET = os.getenv("JWT_SECRET", "justlearnit_secret_change_in_production")
ALGO = "HS256"


def hash_password(p):
    """Return a salted SHA-256 hash of the given plain-text password."""
    salt = os.getenv("PASSWORD_SALT", "jli_salt_2024")
    return hashlib.sha256(f"{salt}{p}".encode()).hexdigest()


def create_token(data):
    """Create a signed JWT that expires in 6 hours."""
    p = data.copy()
    p["exp"] = datetime.now(timezone.utc) + timedelta(hours=6)
    return jwt.encode(p, SECRET, algorithm=ALGO)


def verify_token(token):
    """Decode and return the JWT payload, or None if invalid/expired."""
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGO])
    except JWTError:
        return None


def auth_required(authorization: str = Header(...)):
    """
    FastAPI dependency: validates the Bearer token and checks that the
    user and their school are not blocked or deactivated.
    Returns the decoded JWT payload on success.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid token format")
    payload = verify_token(authorization.split(" ")[1])
    if not payload:
        raise HTTPException(401, "Invalid or expired token")
    from core.db import get_conn
    with get_conn() as (conn, c):
        c.execute("SELECT is_blocked FROM users WHERE id=%s", (payload.get("id"),))
        row = c.fetchone()
        if not row:
            raise HTTPException(401, "User not found")
        if row[0]:
            raise HTTPException(403, "Your account has been blocked. Please contact your school.")
        sid = payload.get("school_id")
        if sid:
            c.execute("SELECT is_blocked,is_active FROM schools WHERE id=%s", (sid,))
            s = c.fetchone()
            if s and (s[0] or not s[1]):
                raise HTTPException(403, "Your school's access has been suspended.")
    return payload


def student_required(u=Depends(auth_required)):
    """FastAPI dependency: requires the caller to have the 'student' role (or admin)."""
    if u.get("role") not in ("student", "admin"):
        raise HTTPException(403, "Student permission required")
    return u


def teacher_required(u=Depends(auth_required)):
    """FastAPI dependency: requires the caller to have the 'teacher' role (or admin)."""
    if u.get("role") not in ("teacher", "admin"):
        raise HTTPException(403, "Teacher permission required")
    return u


def admin_required(u=Depends(auth_required)):
    """FastAPI dependency: requires the caller to have the 'admin' role."""
    if u.get("role") != "admin":
        raise HTTPException(403, "Admin permission required")
    return u


def teacher_or_admin(u=Depends(auth_required)):
    """FastAPI dependency: allows access for both teachers and admins."""
    if u.get("role") not in ("teacher", "admin"):
        raise HTTPException(403, "Insufficient permissions")
    return u


def get_school_filter(u):
    """
    Return the school_id to use as a WHERE filter, or None for admins
    who have unrestricted access across all schools.
    """
    return None if u.get("role") == "admin" else u.get("school_id")
