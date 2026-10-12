"""
JustLearnIt - Database & Migration Manager

Handles database connection, table creation, migrations,
and initial seed data for subjects, market items, and the admin user.
"""
import psycopg2, os, hashlib
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()
DB_URL = os.getenv("DB_URL")


@contextmanager
def get_conn():
    """Context manager that yields a (connection, cursor) tuple and ensures cleanup."""
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    try:
        yield conn, cursor
    finally:
        cursor.close()
        conn.close()


def init_db():
    """Create all tables if they don't exist, run migrations, and seed initial data."""
    with get_conn() as (conn, c):

        # 1. Schools
        c.execute("""CREATE TABLE IF NOT EXISTS schools (
            id SERIAL PRIMARY KEY, name TEXT NOT NULL UNIQUE,
            city TEXT, district TEXT, phone TEXT, email TEXT,
            is_active BOOLEAN DEFAULT TRUE, is_blocked BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW())""")

        # 2. Users
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('student','teacher','admin')),
            school_id INTEGER REFERENCES schools(id) ON DELETE SET NULL,
            is_blocked BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW())""")

        # 3. Students
        c.execute("""CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            school_id INTEGER REFERENCES schools(id) ON DELETE SET NULL,
            full_name TEXT NOT NULL, class_name TEXT,
            class_level INTEGER DEFAULT 9,
            education_level TEXT DEFAULT 'high_school'
                CHECK (education_level IN ('primary','middle','high_school')),
            score INTEGER DEFAULT 0, gold INTEGER DEFAULT 0, streak INTEGER DEFAULT 0,
            total_correct INTEGER DEFAULT 0, total_wrong INTEGER DEFAULT 0,
            total_solved INTEGER DEFAULT 0,
            success_percentage NUMERIC(5,2) DEFAULT 0.00,
            last_active TIMESTAMPTZ DEFAULT NOW(),
            is_active BOOLEAN DEFAULT TRUE,
            selected_badge TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW())""")

        # 4. Subjects
        c.execute("""CREATE TABLE IF NOT EXISTS subjects (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            education_level TEXT NOT NULL
                CHECK (education_level IN ('primary','middle','high_school')),
            class_level INTEGER NOT NULL,
            display_order INTEGER DEFAULT 0,
            UNIQUE(name, education_level, class_level))""")

        # 5. Topics
        c.execute("""CREATE TABLE IF NOT EXISTS topics (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            class_level INTEGER NOT NULL,
            education_level TEXT DEFAULT 'high_school'
                CHECK (education_level IN ('primary','middle','high_school')),
            subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
            subject TEXT DEFAULT 'Mathematics',
            display_order INTEGER DEFAULT 0,
            UNIQUE(name, class_level, education_level))""")

        # 6. Questions
        c.execute("""CREATE TABLE IF NOT EXISTS questions (
            id SERIAL PRIMARY KEY, question_text TEXT NOT NULL,
            option_a TEXT NOT NULL, option_b TEXT NOT NULL,
            option_c TEXT NOT NULL, option_d TEXT NOT NULL, option_e TEXT,
            correct_answer TEXT NOT NULL,
            class_level INTEGER NOT NULL,
            education_level TEXT DEFAULT 'high_school'
                CHECK (education_level IN ('primary','middle','high_school')),
            topic TEXT NOT NULL,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
            subject TEXT DEFAULT 'Mathematics',
            difficult TEXT DEFAULT 'easy'
                CHECK (difficult IN ('easy','medium','hard')),
            created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ DEFAULT NOW())""")

        # 7. Market items
        c.execute("""CREATE TABLE IF NOT EXISTS market_items (
            id SERIAL PRIMARY KEY, name TEXT NOT NULL,
            description TEXT, price INTEGER NOT NULL, item_type TEXT DEFAULT 'boost')""")

        # 8. Active boosts
        c.execute("""CREATE TABLE IF NOT EXISTS active_boosts (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
            item_name TEXT NOT NULL, multiplier INTEGER DEFAULT 1,
            expires_at TIMESTAMPTZ)""")

        # 9. Match history
        c.execute("""CREATE TABLE IF NOT EXISTS match_history (
            student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
            question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
            answered_at TIMESTAMPTZ DEFAULT NOW(),
            is_correct BOOLEAN DEFAULT FALSE,
            PRIMARY KEY (student_id, question_id))""")

        # 10. Homeworks
        c.execute("""CREATE TABLE IF NOT EXISTS homeworks (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
            title TEXT NOT NULL, description TEXT, due_date DATE,
            is_completed BOOLEAN DEFAULT FALSE,
            created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ DEFAULT NOW())""")

        # 11. Notifications
        c.execute("""CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
            title TEXT NOT NULL, message TEXT, is_read BOOLEAN DEFAULT FALSE,
            homework_id INTEGER REFERENCES homeworks(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ DEFAULT NOW())""")

        # 12. Student badges
        c.execute("""CREATE TABLE IF NOT EXISTS student_badges (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
            badge_name TEXT NOT NULL, awarded_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(student_id, badge_name))""")

        # 13. Per-topic performance stats
        c.execute("""CREATE TABLE IF NOT EXISTS student_topic_stats (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
            topic TEXT NOT NULL, class_level INTEGER,
            total_correct INTEGER DEFAULT 0, total_wrong INTEGER DEFAULT 0,
            total_solved INTEGER DEFAULT 0,
            last_solved_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(student_id, topic, class_level))""")

        # 14. System audit logs
        c.execute("""CREATE TABLE IF NOT EXISTS system_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            username TEXT,
            role TEXT,
            action TEXT NOT NULL,
            target_type TEXT,
            target_id INTEGER,
            detail TEXT,
            ip TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW())""")

        conn.commit()
        _migrate(conn, c)
        _seed_subjects(conn, c)
        _seed_market(conn, c)
        _seed_admin(conn, c)
        print("JustLearnIt DB ready.")


def _migrate(conn, c):
    """Safely add missing columns to existing tables without data loss."""
    cols = [
        ("students", "school_id", "INTEGER REFERENCES schools(id) ON DELETE SET NULL"),
        ("students", "education_level", "TEXT DEFAULT 'high_school'"),
        ("students", "class_level", "INTEGER DEFAULT 9"),
        ("students", "total_correct", "INTEGER DEFAULT 0"),
        ("students", "total_wrong", "INTEGER DEFAULT 0"),
        ("students", "total_solved", "INTEGER DEFAULT 0"),
        ("students", "success_percentage", "NUMERIC(5,2) DEFAULT 0.00"),
        ("students", "is_active", "BOOLEAN DEFAULT TRUE"),
        ("students", "selected_badge", "TEXT"),
        ("users", "school_id", "INTEGER REFERENCES schools(id) ON DELETE SET NULL"),
        ("users", "is_blocked", "BOOLEAN DEFAULT FALSE"),
        ("topics", "education_level", "TEXT DEFAULT 'high_school'"),
        ("topics", "subject", "TEXT DEFAULT 'Mathematics'"),
        ("topics", "display_order", "INTEGER DEFAULT 0"),
        ("topics", "subject_id", "INTEGER REFERENCES subjects(id) ON DELETE SET NULL"),
        ("questions", "education_level", "TEXT DEFAULT 'high_school'"),
        ("questions", "subject", "TEXT DEFAULT 'Mathematics'"),
        ("questions", "subject_id", "INTEGER REFERENCES subjects(id) ON DELETE SET NULL"),
        ("questions", "created_by", "INTEGER REFERENCES users(id) ON DELETE SET NULL"),
        ("questions", "created_at", "TIMESTAMPTZ DEFAULT NOW()"),
        ("match_history", "is_correct", "BOOLEAN DEFAULT FALSE"),
        ("schools", "is_blocked", "BOOLEAN DEFAULT FALSE"),
        ("homeworks", "created_by", "INTEGER REFERENCES users(id) ON DELETE SET NULL"),
    ]
    for table, col, defn in cols:
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {defn}")
            conn.commit()
        except Exception:
            conn.rollback()


def _seed_subjects(conn, c):
    """Seed subjects according to the national curriculum for all class levels and education levels."""
    c.execute("SELECT COUNT(*) FROM subjects")
    if c.fetchone()[0] > 0:
        return

    subjects = [
        # PRIMARY (grades 1-4)
        ("Turkish",          "primary", 1, 1),
        ("Mathematics",      "primary", 1, 2),
        ("Life Studies",     "primary", 1, 3),
        ("Turkish",          "primary", 2, 1),
        ("Mathematics",      "primary", 2, 2),
        ("Life Studies",     "primary", 2, 3),
        ("Turkish",          "primary", 3, 1),
        ("Mathematics",      "primary", 3, 2),
        ("Life Studies",     "primary", 3, 3),
        ("Science",          "primary", 3, 4),
        ("Social Studies",   "primary", 3, 5),
        ("Turkish",          "primary", 4, 1),
        ("Mathematics",      "primary", 4, 2),
        ("Science",          "primary", 4, 3),
        ("Social Studies",   "primary", 4, 4),
        # MIDDLE SCHOOL (grades 5-8)
        ("Turkish",              "middle", 5, 1),
        ("Mathematics",          "middle", 5, 2),
        ("Science",              "middle", 5, 3),
        ("Social Studies",       "middle", 5, 4),
        ("English",              "middle", 5, 5),
        ("Religious Culture",    "middle", 5, 6),
        ("Turkish",              "middle", 6, 1),
        ("Mathematics",          "middle", 6, 2),
        ("Science",              "middle", 6, 3),
        ("Social Studies",       "middle", 6, 4),
        ("English",              "middle", 6, 5),
        ("Religious Culture",    "middle", 6, 6),
        ("Turkish",              "middle", 7, 1),
        ("Mathematics",          "middle", 7, 2),
        ("Science",              "middle", 7, 3),
        ("Social Studies",       "middle", 7, 4),
        ("English",              "middle", 7, 5),
        ("Religious Culture",    "middle", 7, 6),
        ("Turkish",              "middle", 8, 1),
        ("Mathematics",          "middle", 8, 2),
        ("Science",              "middle", 8, 3),
        ("Revolution History",   "middle", 8, 4),
        ("English",              "middle", 8, 5),
        ("Religious Culture",    "middle", 8, 6),
        # HIGH SCHOOL (grades 9-12)
        ("Turkish Language & Literature", "high_school", 9,  1),
        ("Mathematics",                   "high_school", 9,  2),
        ("Physics",                       "high_school", 9,  3),
        ("Chemistry",                     "high_school", 9,  4),
        ("Biology",                       "high_school", 9,  5),
        ("History",                       "high_school", 9,  6),
        ("Geography",                     "high_school", 9,  7),
        ("English",                       "high_school", 9,  8),
        ("Religious Culture",             "high_school", 9,  9),
        ("Turkish Language & Literature", "high_school", 10, 1),
        ("Mathematics",                   "high_school", 10, 2),
        ("Physics",                       "high_school", 10, 3),
        ("Chemistry",                     "high_school", 10, 4),
        ("Biology",                       "high_school", 10, 5),
        ("History",                       "high_school", 10, 6),
        ("Geography",                     "high_school", 10, 7),
        ("English",                       "high_school", 10, 8),
        ("Religious Culture",             "high_school", 10, 9),
        ("Turkish Language & Literature", "high_school", 11, 1),
        ("Mathematics",                   "high_school", 11, 2),
        ("Physics",                       "high_school", 11, 3),
        ("Chemistry",                     "high_school", 11, 4),
        ("Biology",                       "high_school", 11, 5),
        ("History",                       "high_school", 11, 6),
        ("Geography",                     "high_school", 11, 7),
        ("English",                       "high_school", 11, 8),
        ("Turkish Language & Literature", "high_school", 12, 1),
        ("Mathematics",                   "high_school", 12, 2),
        ("Physics",                       "high_school", 12, 3),
        ("Chemistry",                     "high_school", 12, 4),
        ("Biology",                       "high_school", 12, 5),
        ("History",                       "high_school", 12, 6),
        ("Geography",                     "high_school", 12, 7),
        ("English",                       "high_school", 12, 8),
    ]
    c.executemany(
        "INSERT INTO subjects(name,education_level,class_level,display_order) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING",
        subjects
    )
    conn.commit()


def _seed_market(conn, c):
    """Seed the market with default purchasable items if none exist."""
    c.execute("SELECT COUNT(*) FROM market_items")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO market_items(name,description,price,item_type) VALUES(%s,%s,%s,%s)", [
            ("Energy Drink",    "2x points for 24 hours!", 150, "boost"),
            ("Energy Bomb",     "3x points for 24 hours!", 300, "boost"),
            ("Streak Freeze",   "Protect your streak for 2 days!", 100, "protection"),
            ("Gold Badge",      "Shine on your profile for 1 week!", 500, "cosmetic"),
            ("Silver Chest",    "Win 50-400 points/gold!", 75, "chest"),
            ("Gold Chest",      "Win 300-1200 points/gold!", 200, "chest"),
        ])
        conn.commit()


def _seed_admin(conn, c):
    """Create the default admin account if it does not already exist."""
    salt = os.getenv("PASSWORD_SALT", "jli_salt_2024")
    pw = hashlib.sha256(f"{salt}admin123".encode()).hexdigest()
    c.execute(
        "INSERT INTO users(username,password,role) VALUES('admin',%s,'admin') ON CONFLICT DO NOTHING",
        (pw,)
    )
    conn.commit()
