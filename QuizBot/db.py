import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor, connect_timeout=5)

def setup_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS whitelist (
            telegram_id  BIGINT PRIMARY KEY,
            plan         TEXT NOT NULL DEFAULT 'trial',
            quiz_count   INT NOT NULL DEFAULT 0
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("DB CONNECTED ✅")

def get_user(telegram_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM whitelist WHERE telegram_id = %s", (telegram_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def add_user(telegram_id: int, plan: str = 'trial'):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO whitelist (telegram_id, plan, quiz_count)
        VALUES (%s, %s, 0)
        ON CONFLICT (telegram_id) DO NOTHING
    """, (telegram_id, plan))
    conn.commit()
    cur.close()
    conn.close()

def increment_quiz(telegram_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE whitelist SET quiz_count = quiz_count + 1 WHERE telegram_id = %s",
        (telegram_id,)
    )
    conn.commit()
    cur.close()
    conn.close()

PLAN_LIMITS = {
    'trial':     5,
    'plus':      100,
    'pro':       200,
    'suspended': 0,
}

def check_limit(telegram_id: int) -> tuple[bool, str]:
    try:
        user = get_user(telegram_id)
        if not user:
            return False, "whitelist"
        if user['plan'] == 'suspended':
            return False, "suspended"
        limit = PLAN_LIMITS.get(user['plan'], 0)
        if user['quiz_count'] >= limit:
            return False, "limit"
        return True, "ok"
    except Exception as e:
        print(f"check_limit error: {e}")
        return False, "error"
