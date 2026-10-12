"""
JustLearnIt - Analytics Module

Provides class-level stats, school-wide summaries, and
per-topic performance reports for teachers and admins.
"""
from fastapi import APIRouter, Depends
from core.db import get_conn
from core.security import teacher_or_admin, get_school_filter

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/class/{class_name}")
def class_stats(class_name: str, user=Depends(teacher_or_admin)):
    """Return aggregate statistics (count, avg/max/min score, avg success rate) for a class."""
    sf = get_school_filter(user)
    with get_conn() as (conn, c):
        if sf:
            c.execute(
                "SELECT COUNT(*),AVG(score),MAX(score),MIN(score),AVG(success_percentage) "
                "FROM students WHERE class_name=%s AND school_id=%s",
                (class_name, sf)
            )
        else:
            c.execute(
                "SELECT COUNT(*),AVG(score),MAX(score),MIN(score),AVG(success_percentage) "
                "FROM students WHERE class_name=%s",
                (class_name,)
            )
        r = c.fetchone()
    return {
        "total": r[0],
        "avg_score": float(r[1] or 0),
        "max": r[2],
        "min": r[3],
        "avg_success": float(r[4] or 0)
    }


@router.get("/school")
def school_stats(user=Depends(teacher_or_admin)):
    """Return school-wide aggregate statistics including totals for gold, solved questions, and accuracy."""
    sf = get_school_filter(user)
    with get_conn() as (conn, c):
        if sf:
            c.execute(
                "SELECT COUNT(*),AVG(score),SUM(gold),AVG(streak),AVG(success_percentage),"
                "SUM(total_solved),SUM(total_correct),SUM(total_wrong) "
                "FROM students WHERE school_id=%s",
                (sf,)
            )
        else:
            c.execute(
                "SELECT COUNT(*),AVG(score),SUM(gold),AVG(streak),AVG(success_percentage),"
                "SUM(total_solved),SUM(total_correct),SUM(total_wrong) FROM students"
            )
        d = c.fetchone()
    return {
        "total_students": d[0],
        "avg_score": float(d[1] or 0),
        "total_gold": d[2],
        "avg_streak": float(d[3] or 0),
        "avg_success_pct": float(d[4] or 0),
        "total_solved": d[5] or 0,
        "total_correct": d[6] or 0,
        "total_wrong": d[7] or 0
    }


@router.get("/school/topic-report")
def topic_report(user=Depends(teacher_or_admin)):
    """
    Return a per-topic breakdown aggregated across all students in the school.
    Includes total correct, wrong, solved counts and success percentage per topic.
    """
    sf = get_school_filter(user)
    with get_conn() as (conn, c):
        if sf:
            c.execute("""SELECT sts.topic,sts.class_level,SUM(sts.total_correct),SUM(sts.total_wrong),SUM(sts.total_solved),
                CASE WHEN SUM(sts.total_solved)>0 THEN ROUND(SUM(sts.total_correct)::NUMERIC/SUM(sts.total_solved)*100,1) ELSE 0 END
                FROM student_topic_stats sts JOIN students s ON s.id=sts.student_id
                WHERE s.school_id=%s GROUP BY sts.topic,sts.class_level ORDER BY SUM(sts.total_solved) DESC""",
                (sf,))
        else:
            c.execute("""SELECT topic,class_level,SUM(total_correct),SUM(total_wrong),SUM(total_solved),
                CASE WHEN SUM(total_solved)>0 THEN ROUND(SUM(total_correct)::NUMERIC/SUM(total_solved)*100,1) ELSE 0 END
                FROM student_topic_stats GROUP BY topic,class_level ORDER BY SUM(total_solved) DESC""")
        rows = c.fetchall()
    return [
        {
            "topic": r[0], "class_level": r[1],
            "total_correct": r[2], "total_wrong": r[3],
            "total_solved": r[4], "success_pct": float(r[5])
        }
        for r in rows
    ]
