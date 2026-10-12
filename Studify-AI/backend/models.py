from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    display_name = Column(String)
    plan_type = Column(String, default="FREE")  # FREE or PLUS
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    xp_points = Column(Integer, default=0)
    level = Column(Integer, default=1)
    streak_count = Column(Integer, default=0)
    last_action_date = Column(Date, nullable=True)

    quotas = relationship("Quota", back_populates="user", cascade="all, delete-orphan")

class Quota(Base):
    __tablename__ = 'quotas'
    __table_args__ = (UniqueConstraint('user_id', 'date', name='uq_user_date'),)
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(Date, nullable=False)
    flashcard_count = Column(Integer, default=0)
    image_upload_count = Column(Integer, default=0)
    ai_coach_count = Column(Integer, default=0)
    quiz_count = Column(Integer, default=0)
    summary_count = Column(Integer, default=0)

    user = relationship("User", back_populates="quotas")
