import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


def get_connection():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        return conn
    except Exception as e:
        print(f"Database Connection Error: {e}")
        return None


def create_hospital_tables():
    conn = get_connection()
    cur = conn.cursor()
    queries = [
        """
        CREATE TABLE IF NOT EXISTS doctors (
            doctor_id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            birthdate DATE NOT NULL,
            id_no TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id SERIAL PRIMARY KEY,
            full_name VARCHAR(50) NOT NULL,
            doctor_id INTEGER REFERENCES doctors(doctor_id) ON DELETE CASCADE,
            date DATE NOT NULL,
            time TIME NOT NULL,

            id_no VARCHAR(11) NOT NULL,
            phone VARCHAR(20),
            gender VARCHAR(10),
            blood_type VARCHAR(5),
            birth_date DATE,
            medical_history TEXT,

            status VARCHAR(20) DEFAULT 'waiting'
            CHECK (status IN ('waiting', 'in_progress', 'completed', 'cancelled'))
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS staffs (
            staff_id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            birthdate DATE NOT NULL,
            password TEXT NOT NULL,
            id_no TEXT NOT NULL
        );
        """
    ]

    try:
        for query in queries:
            cur.execute(query)
        conn.commit()
    except Exception as e:
        print(f"Table Creation Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    create_hospital_tables()