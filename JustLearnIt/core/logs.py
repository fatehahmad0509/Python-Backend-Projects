"""
JustLearnIt - Action Logger

All modules import from here: from core.logs import log_action
Every meaningful user action is recorded in the system_logs table.
"""
from datetime import datetime
import pytz
from core.db import get_conn

_TR = pytz.timezone("Europe/Istanbul")


def log_action(user, action, target_type=None, target_id=None, detail=None, request=None):
    """
    Write an audit entry to system_logs.

    Args:
        user:        Dict containing 'id', 'username', and 'role'.
        action:      Short string identifier for the action (e.g. 'login', 'question_added').
        target_type: Optional entity type affected (e.g. 'student', 'question').
        target_id:   Optional primary key of the affected entity.
        detail:      Optional human-readable description.
        request:     Optional FastAPI Request object (reserved for future IP logging).
    """
    try:
        now = datetime.now(_TR)
        with get_conn() as (conn, c):
            c.execute("""INSERT INTO system_logs(user_id,username,role,action,target_type,target_id,detail,created_at)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",
                (user.get("id"), user.get("username"), user.get("role"),
                 action, target_type, target_id, detail, now))
            conn.commit()
    except Exception:
        # Log failures must never crash the caller
        pass
