from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_plus = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    streak = Column(Integer, default=0)
    last_recipe_date = Column(Date, nullable=True)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    goal = Column(String, nullable=True)  # "weight_gain" or "weight_loss"
    daily_calorie_goal = Column(Integer, nullable=True)

    limits = relationship("UsageLimit", back_populates="user")
    chefbot_limits = relationship("ChefBotLimit", back_populates="user")
    calorie_photo_limits = relationship("CaloriePhotoLimit", back_populates="user")

class UsageLimit(Base):
    __tablename__ = "usage_limits"
    __table_args__ = (Index("ix_usage_limits_user_date", "user_id", "date"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, nullable=False)
    count = Column(Integer, default=0)

    user = relationship("User", back_populates="limits")

class ChefBotLimit(Base):
    __tablename__ = "chefbot_limits"
    __table_args__ = (Index("ix_chefbot_limits_user_date", "user_id", "date"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, nullable=False)
    count = Column(Integer, default=0)

    user = relationship("User", back_populates="chefbot_limits")

class FoodCard(Base):
    __tablename__ = "food_cards"
    __table_args__ = (Index("ix_food_cards_is_diet", "is_diet"),)

    id = Column(Integer, primary_key=True, index=True)
    food_name = Column(String, nullable=False)
    is_diet = Column(Boolean, default=False)

class FoodSuggestLimit(Base):
    __tablename__ = "food_suggest_limits"
    __table_args__ = (Index("ix_food_suggest_limits_user_date", "user_id", "date"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, nullable=False)
    count = Column(Integer, default=0)

class CaloriePhotoLimit(Base):
    __tablename__ = "calorie_photo_limits"
    __table_args__ = (Index("ix_calorie_photo_limits_user_date", "user_id", "date"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, nullable=False)
    count = Column(Integer, default=0)

    user = relationship("User", back_populates="calorie_photo_limits")

class PromoCode(Base):
    __tablename__ = "promo_codes"
    __table_args__ = (Index("ix_promo_codes_code", "code"),)

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    reward_type = Column(String, nullable=False)  # "xp" or "limit_reset"
    reward_value = Column(Integer, default=0)  # XP amount if reward_type=xp
    remaining_uses = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)

class RedeemedCode(Base):
    __tablename__ = "redeemed_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    promo_code_id = Column(Integer, ForeignKey("promo_codes.id", ondelete="CASCADE"), nullable=False)
    redeemed_at = Column(DateTime, default=datetime.utcnow)

