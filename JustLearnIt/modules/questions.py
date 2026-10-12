"""
JustLearnIt - Questions Module (Student Side)

Exposes endpoints for retrieving subjects, topics, and randomized questions.
Topic filtering is performed by subject_id.
Correct answers are intentionally omitted from responses — answer checking
is handled server-side via /match/submit.
"""
import random
from fastapi import APIRouter, Depends, HTTPException, Query
from core.db import get_conn
from core.security import auth_required

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.get("/subjects")
def get_subjects(
    class_level: int = Query(..., alias="class"),
    education_level: str = Query("high_school"),
    user=Depends(auth_required)
):
    """Return all subjects available for the given class level and education level."""
    with get_conn() as (conn, c):
        c.execute("""
            SELECT s.id, s.name, COUNT(t.id) as topic_count
            FROM subjects s
            LEFT JOIN topics t ON t.subject_id = s.id
            WHERE s.class_level = %s AND s.education_level = %s
            GROUP BY s.id, s.name
            ORDER BY s.display_order, s.name
        """, (class_level, education_level))
        rows = c.fetchall()
    return [{"id": r[0], "name": r[1], "topic_count": r[2]} for r in rows]


@router.get("/topics")
def get_topics(
    class_level: int = Query(..., alias="class"),
    education_level: str = Query("high_school"),
    subject_id: int = Query(None),
    user=Depends(auth_required)
):
    """
    Return topics for the given class and education level.
    If subject_id is provided, results are filtered to that subject only.
    """
    with get_conn() as (conn, c):
        if subject_id:
            c.execute("""
                SELECT t.id, t.name, COUNT(q.id) as qcount
                FROM topics t
                LEFT JOIN questions q
                    ON q.topic = t.name
                    AND q.class_level = t.class_level
                    AND q.education_level = t.education_level
                    AND q.subject_id = %s
                WHERE t.class_level = %s
                    AND t.education_level = %s
                    AND t.subject_id = %s
                GROUP BY t.id, t.name
                ORDER BY t.display_order, t.name
            """, (subject_id, class_level, education_level, subject_id))
        else:
            c.execute("""
                SELECT t.id, t.name, COUNT(q.id) as qcount
                FROM topics t
                LEFT JOIN questions q
                    ON q.topic = t.name
                    AND q.class_level = t.class_level
                    AND q.education_level = t.education_level
                WHERE t.class_level = %s AND t.education_level = %s
                GROUP BY t.id, t.name
                ORDER BY t.display_order, t.name
            """, (class_level, education_level))
        rows = c.fetchall()
    return [{"id": r[0], "topic": r[1], "question_count": r[2]} for r in rows]


@router.get("/")
def get_questions(
    class_level: int = Query(..., alias="class"),
    topic_id: int = Query(...),
    education_level: str = Query("high_school"),
    subject_id: int = Query(None),
    limit: int = Query(10, ge=1, le=50),
    user=Depends(auth_required)
):
    """
    Return a random selection of questions for the given topic.
    Correct answers are excluded from the response for security;
    answer validation happens in /match/submit.
    """
    with get_conn() as (conn, c):
        c.execute(
            "SELECT name FROM topics WHERE id = %s AND class_level = %s AND education_level = %s",
            (topic_id, class_level, education_level)
        )
        topic = c.fetchone()
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        if subject_id:
            c.execute("""
                SELECT id FROM questions
                WHERE class_level = %s AND topic = %s
                    AND education_level = %s AND subject_id = %s
            """, (class_level, topic[0], education_level, subject_id))
        else:
            c.execute("""
                SELECT id FROM questions
                WHERE class_level = %s AND topic = %s AND education_level = %s
            """, (class_level, topic[0], education_level))
        ids = [r[0] for r in c.fetchall()]

    if not ids:
        raise HTTPException(status_code=404, detail="No questions found for this topic")

    sel = random.sample(ids, min(limit, len(ids)))
    with get_conn() as (conn, c):
        c.execute("""
            SELECT id, question_text, option_a, option_b, option_c, option_d, option_e
            FROM questions WHERE id = ANY(%s)
        """, (sel,))
        rows = c.fetchall()

    return [
        {
            "id": r[0], "question": r[1],
            "options": {
                "a": r[2], "b": r[3], "c": r[4], "d": r[5],
                **( {"e": r[6]} if r[6] else {})
            }
        }
        for r in rows
    ]
