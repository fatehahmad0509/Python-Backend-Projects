import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    url = os.environ.get("DATABASE_URL")
    if not url or url == "DATABASE_URL":
        raise ValueError("HATA: DATABASE_URL tanımlanmamış!")
        
    conn = psycopg2.connect(url, sslmode="require")
    
    cur = conn.cursor()
    cur.execute("SET TIME ZONE 'Europe/Istanbul';")
    cur.close()
    
    return conn



def _get_columns(cursor, table_name):
    """Verilen tablonun kolon isimlerini liste olarak döner."""
    cursor.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}' 
        AND table_schema = 'public'
    """)
    return [r[0] for r in cursor.fetchall()]


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)
    conn.commit()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    )
    """)
    conn.commit()

    # ── Migration: rename old columns room_id→id and room_name→name ──
    cols = _get_columns(cur, 'rooms')
    if 'room_id' in cols and 'id' not in cols:
        cur.execute("ALTER TABLE rooms RENAME COLUMN room_id TO id")
        print("[migration] rooms.room_id → rooms.id")
    if 'room_name' in cols and 'name' not in cols:
        cur.execute("ALTER TABLE rooms RENAME COLUMN room_name TO name")
        print("[migration] rooms.room_name → rooms.name")
    conn.commit()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY,
        room_id INTEGER NOT NULL,
        nick TEXT NOT NULL,
        text TEXT NOT NULL,
        edited BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)
    conn.commit()

    # ── Migration: edited kolonu ekle (tablo oluştuktan sonra kolonları çek)
    msg_cols = _get_columns(cur, 'messages')
    if 'edited' not in msg_cols:
        cur.execute("ALTER TABLE messages ADD COLUMN edited BOOLEAN DEFAULT FALSE")
        conn.commit()
        print("[migration] messages.edited kolonu eklendi")

    # readers kolonu varsa kaldır
    msg_cols = _get_columns(cur, 'messages')
    if 'readers' in msg_cols:
        cur.execute("ALTER TABLE messages DROP COLUMN readers")
        conn.commit()
        print("[migration] messages.readers kolonu kaldırıldı")

    # ── Push subscriptions ──────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS push_subscriptions (
        id         SERIAL PRIMARY KEY,
        nick       TEXT NOT NULL,
        endpoint   TEXT UNIQUE NOT NULL,
        p256dh     TEXT NOT NULL,
        auth       TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    # ── App settings (key-value, used for auto-generated VAPID keys) ────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS app_settings (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


def get_all_usernames() -> list[str]:
    """Tüm kayıtlı kullanıcı adlarını döner."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users ORDER BY username")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]


def get_rooms():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, name FROM rooms ORDER BY id DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def create_room(name: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO rooms (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
        (name,)
    )
    conn.commit()
    cur.close()
    conn.close()


def get_messages(room_id: int):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    info_cur = conn.cursor()
    info_cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'messages' AND table_schema = 'public'
    """)
    cols = [r[0] for r in info_cur.fetchall()]
    info_cur.close()

    nick_col = next((c for c in cols if c in (
        'nick', 'nickname', 'sender', 'username', 'user_name', 'author')), None)
    text_col = next((c for c in cols if c in (
        'text', 'message_text', 'message', 'content', 'body', 'msg')), None)
    room_col = next((c for c in cols if c in (
        'room_id', 'room', 'room_fk')), None)
    time_col = next((c for c in cols if c in (
        'created_at', 'sent_at', 'timestamp', 'created')), None)
    pk_col   = next((c for c in cols if c in (
        'id', 'message_id', 'msg_id', 'pk')), None) or cols[0]

    if not nick_col or not text_col or not room_col:
        cur.close()
        conn.close()
        raise ValueError(
            f"messages tablosunda beklenen kolonlar bulunamadı. "
            f"Mevcut kolonlar: {cols}. "
            f"nick_col={nick_col}, text_col={text_col}, room_col={room_col}"
        )

    time_expr = f"m.{time_col}::text AS created_at" if time_col else "NOW()::text AS created_at"

    cur.execute(f"""
        SELECT
            m.{pk_col}   AS id,
            m.{nick_col} AS nick,
            m.{text_col} AS text,
            {time_expr},
            COALESCE(m.edited, FALSE) AS edited
        FROM messages m
        WHERE m.{room_col} = %s
        ORDER BY m.{pk_col} ASC
    """, (room_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def create_user(username: str):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username) VALUES (%s) ON CONFLICT (username) DO NOTHING", (username,))
        conn.commit()
    finally:
        cur.close()
        conn.close()


def save_message(room_id: int, nick: str, text: str) -> int:
    conn = get_conn()
    cur = conn.cursor()

    cols = _get_columns(cur, 'messages')
    nick_col = next((c for c in cols if c in (
        'nick', 'nickname', 'sender', 'username', 'user_name', 'author')), 'nick')
    text_col = next((c for c in cols if c in (
        'text', 'message_text', 'message', 'content', 'body', 'msg')), 'text')
    room_col = next((c for c in cols if c in (
        'room_id', 'room', 'room_fk')), 'room_id')

    cur.execute(
        f"INSERT INTO messages ({room_col}, {nick_col}, {text_col}) VALUES (%s, %s, %s) RETURNING id",
        (room_id, nick, text)
    )
    msg_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()
    return msg_id


# ─── Okunma Kaydı ─────────────────────────────────────────────────────────────

def get_message_room(message_id: int) -> int | None:
    """Mesajın ait olduğu room_id'yi döner."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT room_id FROM messages WHERE id = %s", (message_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


def delete_message(message_id: int, nick: str) -> bool:
    """Mesajı sil. Sadece sahibi silebilir. Başarılıysa True döner."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE id = %s AND nick = %s", (message_id, nick))
    deleted = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return deleted


def edit_message(message_id: int, nick: str, new_text: str) -> bool:
    """Mesajı düzenle. Sadece sahibi düzenleyebilir. Başarılıysa True döner."""
    conn = get_conn()
    cur = conn.cursor()

    # edited sütunu yoksa ekle (migration)
    cols = _get_columns(cur, 'messages')
    if 'edited' not in cols:
        cur.execute("ALTER TABLE messages ADD COLUMN edited BOOLEAN DEFAULT FALSE")
        conn.commit()

    cur.execute(
        "UPDATE messages SET text = %s, edited = TRUE WHERE id = %s AND nick = %s",
        (new_text, message_id, nick)
    )
    updated = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return updated




# ─── Push Subscription Helpers ────────────────────────────────────────────────

def save_subscription(nick: str, endpoint: str, p256dh: str, auth: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO push_subscriptions (nick, endpoint, p256dh, auth)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (endpoint) DO UPDATE
            SET nick   = EXCLUDED.nick,
                p256dh = EXCLUDED.p256dh,
                auth   = EXCLUDED.auth
    """, (nick, endpoint, p256dh, auth))
    conn.commit()
    cur.close()
    conn.close()


def get_subscriptions_to_notify(sender_nick: str, connected_nicks: set) -> list:
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    exclude = tuple(connected_nicks | {sender_nick})
    cur.execute(
        "SELECT nick, endpoint, p256dh, auth FROM push_subscriptions WHERE nick NOT IN %s",
        (exclude,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def delete_subscription(endpoint: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM push_subscriptions WHERE endpoint = %s", (endpoint,))
    conn.commit()
    cur.close()
    conn.close()


def get_room_name(room_id: int) -> str:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM rooms WHERE id = %s", (room_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else f"room-{room_id}"


# ─── App Settings ─────────────────────────────────────────────────────────────

def get_setting(key: str, default: str = "") -> str:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM app_settings WHERE key = %s", (key,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else default


def set_setting(key: str, value: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO app_settings (key, value) VALUES (%s, %s)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """, (key, value))
    conn.commit()
    cur.close()
    conn.close()
