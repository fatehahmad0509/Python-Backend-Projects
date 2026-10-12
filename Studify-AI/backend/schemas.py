from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import List, Optional

class UserInfo(BaseModel):
    id: int
    email: str
    display_name: str
    plan_type: str
    joined_at: datetime
    xp_points: int = 0
    level: int = 1
    streak_count: int = 0
    model_config = ConfigDict(from_attributes=True)

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    display_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo

class XpNotification(BaseModel):
    xp_earned: int
    total_xp: int
    level: int
    leveled_up: bool = False
    streak_count: int = 0

class FlashcardCreate(BaseModel):
    front_text: str
    back_text: str

class FlashcardResponse(BaseModel):
    front_text: str
    back_text: str

class FlashcardGenerateResponse(BaseModel):
    cards: List[FlashcardResponse]
    xp_notification: Optional[XpNotification] = None

class FlashcardGenerateRequest(BaseModel):
    notes_text: str
    count: int = 5

class SolverResponse(BaseModel):
    extracted_text: str
    solution: str
    xp_notification: Optional[XpNotification] = None

class SummaryRequest(BaseModel):
    content: str
    content_type: str = "text"

class SummaryResponse(BaseModel):
    title: str
    content: str
    xp_notification: Optional[XpNotification] = None

class QuizGenerateRequest(BaseModel):
    subject: str
    grade_level: str
    topic: str
    question_count: int = 5

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: int
    explanation: str

class QuizResponse(BaseModel):
    questions: List[QuizQuestion]
    subject: str
    topic: str
    xp_notification: Optional[XpNotification] = None



class CoachMessage(BaseModel):
    message: str
    history: List[dict] = []

class CoachResponse(BaseModel):
    reply: str
    xp_notification: Optional[XpNotification] = None

class QuotaInfo(BaseModel):
    flashcard_count: int
    flashcard_limit: int
    image_upload_count: int
    image_upload_limit: int
    ai_coach_count: int
    ai_coach_limit: int
    quiz_count: int
    quiz_limit: int
    summary_count: int
    summary_limit: int

class ProfileResponse(BaseModel):
    user: UserInfo
    quotas: QuotaInfo
    xp_current_level: int = 0
    xp_to_next_level: int = 100

class LeaderboardEntry(BaseModel):
    rank: int
    display_name: str
    xp_points: int
    level: int
    streak_count: int

class LeaderboardResponse(BaseModel):
    leaders: List[LeaderboardEntry]
    user_rank: Optional[int] = None


