
# Pydantic schemas for request/response validation and serialization
from datetime import datetime, date
from typing import Any, List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    full_name: Optional[str] = None
    native_language_code: Optional[str] = "tr"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=128)


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    native_language_code: Optional[str] = None
    daily_goal_xp: Optional[int] = None
    level_code: Optional[str] = None


class UserOut(BaseModel):
    # Public-facing user profile returned by the API
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_admin: bool
    active_language_code: Optional[str] = None
    native_language_code: str
    level_code: str
    xp_total: int
    hearts: int
    max_hearts: int
    gems: int
    streak_days: int
    longest_streak: int
    daily_goal_xp: int
    daily_xp_earned: int
    league_tier: str
    league_xp_week: int
    created_at: datetime


class LanguageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    code: str
    name: str
    native_name: str
    flag_emoji: str
    is_active: bool
    order_index: int


class LanguageCreate(BaseModel):
    code: str
    name: str
    native_name: str
    flag_emoji: str
    order_index: int = 0
    is_active: bool = True


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    order_index: int
    title: str
    description: Optional[str] = None
    xp_reward: int
    icon: str
    is_ai_dynamic: bool
    topic: Optional[str] = None
    completed: bool = False
    best_accuracy: float = 0.0


class SectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    order_index: int
    title: str
    description: Optional[str] = None
    lessons: List[LessonOut] = []


class UnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    order_index: int
    title: str
    description: Optional[str] = None
    color: str
    icon: str
    cefr_level: str
    sections: List[SectionOut] = []


class UnitCreate(BaseModel):
    language_id: str
    title: str
    description: Optional[str] = None
    color: str = "#8B5CF6"
    icon: str = "Sparkles"
    cefr_level: str = "A1"
    order_index: int = 0


class SectionCreate(BaseModel):
    unit_id: str
    title: str
    description: Optional[str] = None
    order_index: int = 0


class LessonCreate(BaseModel):
    section_id: str
    title: str
    description: Optional[str] = None
    xp_reward: int = 10
    icon: str = "BookOpen"
    is_ai_dynamic: bool = False
    topic: Optional[str] = None
    order_index: int = 0


class QuestionOut(BaseModel):
    # Question shown to the user (without the correct answer)
    model_config = ConfigDict(from_attributes=True)
    id: str
    order_index: int
    type: str
    prompt: str
    prompt_translation: Optional[str] = None
    data: Any
    explanation: Optional[str] = None


class QuestionAdminOut(QuestionOut):
    # Admin version includes the correct answer
    correct_answer: str


class QuestionCreate(BaseModel):
    lesson_id: str
    type: str
    prompt: str
    prompt_translation: Optional[str] = None
    data: Any
    correct_answer: str
    explanation: Optional[str] = None
    order_index: int = 0


class AnswerSubmit(BaseModel):
    question_id: Optional[str] = None
    lesson_id: Optional[str] = None
    question_type: str
    prompt: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    language_code: Optional[str] = None
    topic: Optional[str] = None


class LessonCompleteRequest(BaseModel):
    lesson_id: str
    correct_count: int
    total_count: int
    hearts_lost: int = 0
    duration_seconds: int = 0


class LessonCompleteResponse(BaseModel):
    xp_earned: int
    streak_days: int
    daily_xp_earned: int
    daily_goal_xp: int
    new_level: bool = False
    new_achievements: List["AchievementOut"] = []
    hearts: int


class AchievementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    code: str
    title: str
    description: str
    icon: str
    color: str
    condition_type: str
    condition_value: int
    xp_reward: int
    unlocked: bool = False
    unlocked_at: Optional[datetime] = None


class DailyQuestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    quest_type: str
    title: str
    target: int
    progress: int
    completed: bool
    xp_reward: int
    icon: str


class DailyXPPoint(BaseModel):
    date: date
    xp: int


class UserStats(BaseModel):
    xp_total: int
    streak_days: int
    longest_streak: int
    lessons_completed: int
    words_learned: int
    accuracy: float
    total_answers: int
    correct_answers: int
    daily_xp: List[DailyXPPoint]
    level_code: str
    league_tier: str
    league_xp_week: int


class LeaderboardEntry(BaseModel):
    user_id: str
    username: str
    avatar_url: Optional[str] = None
    xp_week: int
    streak_days: int
    rank: int


class LeaderboardOut(BaseModel):
    tier: str
    week_start: date
    entries: List[LeaderboardEntry]
    my_rank: Optional[int] = None


class AIChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    session_kind: str = "teacher"
    language_code: Optional[str] = None
    lesson_context: Optional[str] = None


class AIChatMessage(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime


class AIChatResponse(BaseModel):
    session_id: str
    reply: str
    messages: List[AIChatMessage]


class AIExplainWrongRequest(BaseModel):
    language_code: str
    question_type: str
    prompt: str
    correct_answer: str
    user_answer: str


class AIExplainWrongResponse(BaseModel):
    explanation: str
    correction_hint: str
    examples: List[str]


class AIWordExplainRequest(BaseModel):
    word: str
    language_code: str
    native_language_code: Optional[str] = "tr"


class AIWordExplainResponse(BaseModel):
    word: str
    meaning: str
    pronunciation: str
    part_of_speech: Optional[str] = None
    synonyms: List[str] = []
    antonyms: List[str] = []
    examples: List[dict] = []
    tips: Optional[str] = None


class AIQuizGenerateRequest(BaseModel):
    language_code: str
    level_code: Optional[str] = "A1"
    topic: Optional[str] = None
    num_questions: int = 5
    types: Optional[List[str]] = None


class GeneratedQuestion(BaseModel):
    type: str
    prompt: str
    prompt_translation: Optional[str] = None
    data: Any
    correct_answer: str
    explanation: str


class AIQuizGenerateResponse(BaseModel):
    language_code: str
    level_code: str
    topic: Optional[str] = None
    questions: List[GeneratedQuestion]


class AITranslateRequest(BaseModel):
    text: str
    source_language_code: Optional[str] = None
    target_language_code: str


class AITranslateResponse(BaseModel):
    translation: str
    explanation: str
    grammar_notes: Optional[str] = None


class AdminUserOut(UserOut):
    pass


class AdminUpdateUserRequest(BaseModel):
    is_admin: Optional[bool] = None
    hearts: Optional[int] = None
    gems: Optional[int] = None
    xp_total: Optional[int] = None
    league_tier: Optional[str] = None


TokenResponse.model_rebuild()
LessonCompleteResponse.model_rebuild()
