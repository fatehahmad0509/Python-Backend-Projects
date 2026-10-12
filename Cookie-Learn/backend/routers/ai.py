
# AI-powered routes: chat (teacher/practice modes), explanation of wrong answers, word lookup, quiz generation, translation
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import ai_service
from database import get_db
from models import ChatMessage, User, UserAnswer
from schemas import (
    AIChatMessage, AIChatRequest, AIChatResponse, AIExplainWrongRequest, AIExplainWrongResponse,
    AIQuizGenerateRequest, AIQuizGenerateResponse, AITranslateRequest, AITranslateResponse,
    AIWordExplainRequest, AIWordExplainResponse, GeneratedQuestion,
)
from security import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])


def _history_for(db: Session, user_id: str, session_id: str, limit: int = 20) -> list[dict]:
    # Fetch recent chat message history for a given session
    msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id, ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    msgs = list(reversed(msgs))
    return [{"role": m.role, "content": m.content} for m in msgs]


@router.post("/chat", response_model=AIChatResponse)
def ai_chat(body: AIChatRequest, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Send a message to the AI teacher or practice partner and get a response
    session_id = body.session_id or f"{body.session_kind}-{uuid.uuid4().hex[:12]}"
    lang = body.language_code or current.active_language_code or "en"
    history = _history_for(db, current.id, session_id)
    try:
        if body.session_kind == "practice":
            reply = ai_service.chat_practice(history, body.message, lang, current.native_language_code)
        else:
            reply = ai_service.chat_teacher(history, body.message, lang, current.native_language_code)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    user_msg = ChatMessage(
        user_id=current.id, session_id=session_id, session_kind=body.session_kind,
        role="user", content=body.message, language_code=lang,
    )
    ai_msg = ChatMessage(
        user_id=current.id, session_id=session_id, session_kind=body.session_kind,
        role="assistant", content=reply, language_code=lang,
    )
    db.add_all([user_msg, ai_msg])
    db.commit()
    db.refresh(user_msg)
    db.refresh(ai_msg)

    msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current.id, ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return AIChatResponse(
        session_id=session_id,
        reply=reply,
        messages=[
            AIChatMessage(id=m.id, role=m.role, content=m.content, created_at=m.created_at) for m in msgs
        ],
    )


@router.get("/chat/sessions")
def list_sessions(
    session_kind: str = Query("teacher"),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # List distinct chat sessions for the current user, with the most recent message preview
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current.id, ChatMessage.session_kind == session_kind)
        .order_by(ChatMessage.created_at.desc())
        .all()
    )
    seen: dict[str, dict] = {}
    for m in rows:
        if m.session_id not in seen:
            seen[m.session_id] = {
                "session_id": m.session_id,
                "last_message": m.content[:120],
                "last_at": m.created_at,
                "language_code": m.language_code,
            }
    return list(seen.values())


@router.get("/chat/{session_id}", response_model=List[AIChatMessage])
def get_chat_messages(session_id: str, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get all messages for a specific chat session
    msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current.id, ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return [AIChatMessage(id=m.id, role=m.role, content=m.content, created_at=m.created_at) for m in msgs]


@router.post("/explain-wrong", response_model=AIExplainWrongResponse)
def explain_wrong(body: AIExplainWrongRequest, current: User = Depends(get_current_user)):
    # Get an AI explanation for why the user's answer was incorrect
    try:
        data = ai_service.explain_wrong_answer(
            language_code=body.language_code,
            question_type=body.question_type,
            prompt=body.prompt,
            correct_answer=body.correct_answer,
            user_answer=body.user_answer,
            native_language=current.native_language_code,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return AIExplainWrongResponse(**data)


@router.post("/word", response_model=AIWordExplainResponse)
def word_explain(body: AIWordExplainRequest, current: User = Depends(get_current_user)):
    # Get a detailed AI explanation for a word (meaning, pronunciation, examples, etc.)
    try:
        data = ai_service.explain_word(
            word=body.word,
            language_code=body.language_code,
            native_language=body.native_language_code or current.native_language_code,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return AIWordExplainResponse(**data)


@router.post("/quiz/generate", response_model=AIQuizGenerateResponse)
def quiz_generate(body: AIQuizGenerateRequest, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Generate a set of quiz questions using AI, optionally targeting weak topics
    weak_rows = (
        db.query(UserAnswer.topic)
        .filter(UserAnswer.user_id == current.id, UserAnswer.is_correct == False, UserAnswer.topic.isnot(None))
        .order_by(UserAnswer.created_at.desc())
        .limit(30)
        .all()
    )
    weak_topics = list({r[0] for r in weak_rows if r[0]})[:5]

    def _try_generate() -> list:
        try:
            data = ai_service.generate_quiz(
                language_code=body.language_code,
                level_code=body.level_code or current.level_code,
                topic=body.topic,
                num_questions=max(3, min(body.num_questions, 10)),
                types_wanted=body.types,
                native_language=current.native_language_code,
                weak_topics=weak_topics,
            )
        except RuntimeError as e:
            raise HTTPException(status_code=502, detail=str(e))
        raw = data.get("questions", []) or []
        valid: list[GeneratedQuestion] = []
        for q in raw:
            if not isinstance(q, dict):
                continue
            if not q.get("prompt") or not q.get("correct_answer") or not q.get("type"):
                continue
            try:
                valid.append(GeneratedQuestion(**q))
            except Exception:
                continue
        return valid

    questions = _try_generate()
    if not questions:
        questions = _try_generate()
    if not questions:
        raise HTTPException(status_code=502, detail="AI could not generate valid questions right now, please try again.")

    return AIQuizGenerateResponse(
        language_code=body.language_code,
        level_code=body.level_code or current.level_code,
        topic=body.topic,
        questions=questions,
    )


@router.post("/translate", response_model=AITranslateResponse)
def translate(body: AITranslateRequest, current: User = Depends(get_current_user)):
    # Translate text and provide grammar/usage explanation
    try:
        data = ai_service.translate_and_explain(
            text=body.text,
            target_language_code=body.target_language_code,
            source_language_code=body.source_language_code,
            native_language=current.native_language_code,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return AITranslateResponse(**data)
