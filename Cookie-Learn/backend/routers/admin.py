
# Admin routes: manage languages, units, sections, lessons, questions, and users
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Language, Lesson, Question, Section, Unit, User
from schemas import (
    AdminUpdateUserRequest, AdminUserOut, LanguageCreate, LanguageOut, LessonCreate,
    QuestionAdminOut, QuestionCreate, SectionCreate, UnitCreate, UserOut,
)
from security import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])


@router.post("/languages", response_model=LanguageOut)
def create_language(body: LanguageCreate, db: Session = Depends(get_db)):
    if db.query(Language).filter(Language.code == body.code.lower()).first():
        raise HTTPException(status_code=400, detail="This language code already exists")
    lang = Language(
        code=body.code.lower(), name=body.name, native_name=body.native_name,
        flag_emoji=body.flag_emoji, order_index=body.order_index, is_active=body.is_active,
    )
    db.add(lang)
    db.commit()
    db.refresh(lang)
    return LanguageOut.model_validate(lang)


@router.delete("/languages/{lang_id}")
def delete_language(lang_id: str, db: Session = Depends(get_db)):
    lang = db.query(Language).filter(Language.id == lang_id).first()
    if not lang:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(lang)
    db.commit()
    return {"ok": True}


@router.post("/units")
def create_unit(body: UnitCreate, db: Session = Depends(get_db)):
    u = Unit(**body.model_dump())
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"id": u.id, "title": u.title, "order_index": u.order_index}


@router.delete("/units/{uid}")
def delete_unit(uid: str, db: Session = Depends(get_db)):
    u = db.query(Unit).filter(Unit.id == uid).first()
    if not u:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(u)
    db.commit()
    return {"ok": True}


@router.post("/sections")
def create_section(body: SectionCreate, db: Session = Depends(get_db)):
    s = Section(**body.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"id": s.id, "title": s.title, "unit_id": s.unit_id}


@router.delete("/sections/{sid}")
def delete_section(sid: str, db: Session = Depends(get_db)):
    s = db.query(Section).filter(Section.id == sid).first()
    if not s:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(s)
    db.commit()
    return {"ok": True}


@router.post("/lessons")
def create_lesson(body: LessonCreate, db: Session = Depends(get_db)):
    l = Lesson(**body.model_dump())
    db.add(l)
    db.commit()
    db.refresh(l)
    return {"id": l.id, "title": l.title, "section_id": l.section_id}


@router.delete("/lessons/{lid}")
def delete_lesson(lid: str, db: Session = Depends(get_db)):
    l = db.query(Lesson).filter(Lesson.id == lid).first()
    if not l:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(l)
    db.commit()
    return {"ok": True}


@router.post("/questions", response_model=QuestionAdminOut)
def create_question(body: QuestionCreate, db: Session = Depends(get_db)):
    q = Question(**body.model_dump())
    db.add(q)
    db.commit()
    db.refresh(q)
    return QuestionAdminOut.model_validate(q)


@router.get("/lessons/{lid}/questions", response_model=List[QuestionAdminOut])
def list_lesson_questions(lid: str, db: Session = Depends(get_db)):
    qs = db.query(Question).filter(Question.lesson_id == lid).order_by(Question.order_index).all()
    return [QuestionAdminOut.model_validate(q) for q in qs]


@router.delete("/questions/{qid}")
def delete_question(qid: str, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == qid).first()
    if not q:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(q)
    db.commit()
    return {"ok": True}


@router.get("/users", response_model=List[AdminUserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).limit(500).all()
    return [AdminUserOut.model_validate(u) for u in users]


@router.patch("/users/{uid}", response_model=UserOut)
def update_user(uid: str, body: AdminUpdateUserRequest, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == uid).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(u, k, v)
    db.commit()
    db.refresh(u)
    return UserOut.model_validate(u)


@router.delete("/users/{uid}")
def delete_user(uid: str, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == uid).first()
    if not u:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(u)
    db.commit()
    return {"ok": True}
