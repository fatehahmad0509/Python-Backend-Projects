
# SQLAlchemy ORM models defining the database schema
import uuid
from datetime import datetime, timezone, date
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Date, ForeignKey, Text,
    Float, JSON, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class User(Base):
    # Represents a learner account with gamification stats
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)

    active_language_code = Column(String, nullable=True)
    native_language_code = Column(String, default="tr", nullable=False)
    level_code = Column(String, default="A1", nullable=False)

    # Gamification fields
    xp_total = Column(Integer, default=0, nullable=False)
    hearts = Column(Integer, default=5, nullable=False)
    max_hearts = Column(Integer, default=5, nullable=False)
    last_heart_regen = Column(DateTime(timezone=True), default=_now)
    gems = Column(Integer, default=50, nullable=False)
    streak_days = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)
    last_active_date = Column(Date, nullable=True)
    daily_goal_xp = Column(Integer, default=30, nullable=False)
    daily_xp_earned = Column(Integer, default=0, nullable=False)
    daily_reset_date = Column(Date, nullable=True)

    # League / leaderboard
    league_tier = Column(String, default="bronze", nullable=False)
    league_xp_week = Column(Integer, default=0, nullable=False)
    league_week_start = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    lesson_progress = relationship("UserLessonProgress", back_populates="user", cascade="all, delete-orphan")
    answers = relationship("UserAnswer", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    daily_quests = relationship("DailyQuest", back_populates="user", cascade="all, delete-orphan")


class Language(Base):
    # A language available for learning
    __tablename__ = "languages"
    id = Column(String, primary_key=True, default=_uuid)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    native_name = Column(String, nullable=False)
    flag_emoji = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    units = relationship("Unit", back_populates="language", cascade="all, delete-orphan", order_by="Unit.order_index")


class Unit(Base):
    # A top-level grouping in a language's curriculum (e.g. "Basic Greetings")
    __tablename__ = "units"
    id = Column(String, primary_key=True, default=_uuid)
    language_id = Column(String, ForeignKey("languages.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index = Column(Integer, default=0, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String, default="#8B5CF6", nullable=False)
    icon = Column(String, default="Sparkles", nullable=False)
    cefr_level = Column(String, default="A1", nullable=False)

    language = relationship("Language", back_populates="units")
    sections = relationship("Section", back_populates="unit", cascade="all, delete-orphan", order_by="Section.order_index")


class Section(Base):
    # A section within a unit containing multiple lessons
    __tablename__ = "sections"
    id = Column(String, primary_key=True, default=_uuid)
    unit_id = Column(String, ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index = Column(Integer, default=0, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    unit = relationship("Unit", back_populates="sections")
    lessons = relationship("Lesson", back_populates="section", cascade="all, delete-orphan", order_by="Lesson.order_index")


class Lesson(Base):
    # A lesson containing questions; can be static or AI-generated
    __tablename__ = "lessons"
    id = Column(String, primary_key=True, default=_uuid)
    section_id = Column(String, ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index = Column(Integer, default=0, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    xp_reward = Column(Integer, default=10, nullable=False)
    icon = Column(String, default="BookOpen", nullable=False)
    is_ai_dynamic = Column(Boolean, default=False, nullable=False)
    topic = Column(String, nullable=True)

    section = relationship("Section", back_populates="lessons")
    questions = relationship("Question", back_populates="lesson", cascade="all, delete-orphan", order_by="Question.order_index")


class Question(Base):
    # A single exercise question within a lesson
    __tablename__ = "questions"
    id = Column(String, primary_key=True, default=_uuid)
    lesson_id = Column(String, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index = Column(Integer, default=0, nullable=False)
    type = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    prompt_translation = Column(Text, nullable=True)
    data = Column(JSON, nullable=False)
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)

    lesson = relationship("Lesson", back_populates="questions")


class UserLessonProgress(Base):
    # Tracks a user's completion status for each lesson
    __tablename__ = "user_lesson_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson"),)
    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(String, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    completed = Column(Boolean, default=False, nullable=False)
    best_accuracy = Column(Float, default=0.0, nullable=False)
    best_xp = Column(Integer, default=0, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    user = relationship("User", back_populates="lesson_progress")


class UserAnswer(Base):
    # Records each individual answer a user submits
    __tablename__ = "user_answers"
    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(String, nullable=True, index=True)
    question_type = Column(String, nullable=True)
    prompt = Column(Text, nullable=True)
    user_answer = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, default=False, nullable=False)
    language_code = Column(String, nullable=True)
    topic = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    user = relationship("User", back_populates="answers")


class Achievement(Base):
    # A predefined achievement that users can unlock
    __tablename__ = "achievements"
    id = Column(String, primary_key=True, default=_uuid)
    code = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    icon = Column(String, default="Trophy", nullable=False)
    color = Column(String, default="#F59E0B", nullable=False)
    condition_type = Column(String, nullable=False)
    condition_value = Column(Integer, nullable=False)
    xp_reward = Column(Integer, default=50, nullable=False)


class UserAchievement(Base):
    # Junction table linking users to unlocked achievements
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)
    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id = Column(String, ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False, index=True)
    unlocked_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement")


class DailyQuest(Base):
    # A daily challenge assigned to a user
    __tablename__ = "daily_quests"
    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    quest_date = Column(Date, nullable=False, index=True)
    quest_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    target = Column(Integer, nullable=False)
    progress = Column(Integer, default=0, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    xp_reward = Column(Integer, default=20, nullable=False)
    icon = Column(String, default="Target", nullable=False)

    user = relationship("User", back_populates="daily_quests")


class ChatMessage(Base):
    # A single message in an AI chat session
    __tablename__ = "chat_messages"
    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String, nullable=False, index=True)
    session_kind = Column(String, default="teacher", nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    language_code = Column(String, nullable=True)
    context = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    user = relationship("User", back_populates="chat_messages")


Index("idx_chat_user_session", ChatMessage.user_id, ChatMessage.session_id, ChatMessage.created_at)
Index("idx_answers_user_time", UserAnswer.user_id, UserAnswer.created_at)
