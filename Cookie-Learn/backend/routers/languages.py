
# Language and curriculum routes: list languages, fetch curriculum, get lesson questions, check answers
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import Language, Lesson, Question, Section, Unit, UserLessonProgress, User
from schemas import (
    LanguageOut, LessonOut, QuestionOut, SectionOut, UnitOut,
)
from security import get_current_user

router = APIRouter(prefix="/languages", tags=["languages"])


@router.get("", response_model=List[LanguageOut])
def list_languages(db: Session = Depends(get_db)):
    # Get all active languages ordered by display index
    langs = db.query(Language).filter(Language.is_active == True).order_by(Language.order_index).all()
    return [LanguageOut.model_validate(l) for l in langs]


@router.get("/{code}/curriculum", response_model=List[UnitOut])
def curriculum(code: str, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Fetch the full curriculum tree (units → sections → lessons) for a language,
    # annotated with the current user's completion progress
    lang = db.query(Language).filter(Language.code == code.lower()).first()
    if not lang:
        raise HTTPException(status_code=404, detail="Language not found")
    units = (
        db.query(Unit)
        .filter(Unit.language_id == lang.id)
        .options(selectinload(Unit.sections).selectinload(Section.lessons))
        .order_by(Unit.order_index)
        .all()
    )
    progress = {
        p.lesson_id: p for p in db.query(UserLessonProgress).filter(UserLessonProgress.user_id == current.id).all()
    }
    out: list[UnitOut] = []
    for u in units:
        sections_out: list[SectionOut] = []
        for s in u.sections:
            lessons_out: list[LessonOut] = []
            for l in s.lessons:
                pr = progress.get(l.id)
                lessons_out.append(LessonOut(
                    id=l.id, order_index=l.order_index, title=l.title, description=l.description,
                    xp_reward=l.xp_reward, icon=l.icon, is_ai_dynamic=l.is_ai_dynamic, topic=l.topic,
                    completed=pr.completed if pr else False,
                    best_accuracy=pr.best_accuracy if pr else 0.0,
                ))
            sections_out.append(SectionOut(
                id=s.id, order_index=s.order_index, title=s.title, description=s.description,
                lessons=lessons_out,
            ))
        out.append(UnitOut(
            id=u.id, order_index=u.order_index, title=u.title, description=u.description,
            color=u.color, icon=u.icon, cefr_level=u.cefr_level, sections=sections_out,
        ))
    return out


@router.get("/lessons/{lesson_id}/questions", response_model=List[QuestionOut])
def lesson_questions(lesson_id: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get all questions for a specific lesson (without correct answers exposed)
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    qs = (
        db.query(Question)
        .filter(Question.lesson_id == lesson_id)
        .order_by(Question.order_index)
        .all()
    )
    return [QuestionOut.model_validate(q) for q in qs]


@router.post("/lessons/{lesson_id}/check-answer")
def check_answer(lesson_id: str, payload: dict, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check a user's answer against the stored correct answer for a static lesson question
    question_id = payload.get("question_id")
    user_answer = (payload.get("user_answer") or "").strip()
    q = db.query(Question).filter(Question.id == question_id, Question.lesson_id == lesson_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    ca = q.correct_answer.strip()
    is_correct = _compare_answer(q.type, ca, user_answer)
    return {"is_correct": is_correct, "correct_answer": ca, "explanation": q.explanation}


def _compare_answer(qtype: str, correct: str, given: str) -> bool:
    # Compare user's answer with the correct answer, normalizing case and punctuation
    if not given:
        return False
    c = correct.strip().lower()
    g = given.strip().lower()
    if qtype in {"multiple_choice", "word_match"}:
        return c == g
    normalize = lambda s: "".join(ch for ch in s if ch.isalnum() or ch.isspace()).strip()
    return normalize(c) == normalize(g)
