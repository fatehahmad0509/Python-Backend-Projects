import os
import sys

# ── Env kontrolleri (önce, import'lardan önce) ────────────────────────────────
REQUIRED_ENV = {
    "DATABASE_URL": "PostgreSQL bağlantı adresi",
    "JWT_SECRET": "JWT imzalama anahtarı",
    "GEMINI_API_KEY": "Google Gemini API anahtarı",
}
missing = [f"  {k} -> {v}" for k, v in REQUIRED_ENV.items() if not os.environ.get(k)]
if missing:
    print("=" * 60, file=sys.stderr)
    print("HATA: Aşağıdaki ortam değişkenleri (env) eksik:", file=sys.stderr)
    print("\n".join(missing), file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    sys.exit(1)

import random
import threading
import time
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from pydantic import BaseModel
from google import genai
from google.genai import types
import db
import models
import auth
import ai

chefbot_key = os.environ.get("GEMINI_CHEFBOT_API_KEY") or os.environ.get("GEMINI_API_KEY")
chefbot_client = genai.Client(api_key=chefbot_key)

# Initialize DB tables
models.Base.metadata.create_all(bind=db.engine)

# Startup migration for new columns on existing tables
def run_startup_migration():
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS goal VARCHAR"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_calorie_goal INTEGER"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_usage_limits_user_date ON usage_limits (user_id, date)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_chefbot_limits_user_date ON chefbot_limits (user_id, date)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_food_suggest_limits_user_date ON food_suggest_limits (user_id, date)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_calorie_photo_limits_user_date ON calorie_photo_limits (user_id, date)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_food_cards_is_diet ON food_cards (is_diet)"))
            conn.execute(text("CREATE TABLE IF NOT EXISTS promo_codes (id SERIAL PRIMARY KEY, code VARCHAR UNIQUE NOT NULL, reward_type VARCHAR NOT NULL, reward_value INTEGER DEFAULT 0, remaining_uses INTEGER DEFAULT 1, is_active BOOLEAN DEFAULT TRUE)"))
            conn.execute(text("CREATE TABLE IF NOT EXISTS redeemed_codes (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), promo_code_id INTEGER NOT NULL REFERENCES promo_codes(id) ON DELETE CASCADE, redeemed_at TIMESTAMP DEFAULT NOW())"));
            # Mevcut FK constraint'ine CASCADE ekle (tablo zaten varsa)
            try:
                conn.execute(text("ALTER TABLE redeemed_codes DROP CONSTRAINT IF EXISTS redeemed_codes_promo_code_id_fkey, ADD CONSTRAINT redeemed_codes_promo_code_id_fkey FOREIGN KEY (promo_code_id) REFERENCES promo_codes(id) ON DELETE CASCADE"))
            except Exception:
                pass
            conn.commit()
    except Exception as e:
        print(f"Migration not needed or failed (non-critical): {e}")

run_startup_migration()

from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import Response

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Mr.Food API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://mr-food-i4qr.onrender.com"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Limit tabloları temizleme (3 günden eski kayıtlar) ────────────────────────
def cleanup_old_limits():
    while True:
        try:
            with db.SessionLocal() as session:
                cutoff = get_turkey_date() - timedelta(days=3)
                session.query(models.UsageLimit).filter(models.UsageLimit.date < cutoff).delete()
                session.query(models.ChefBotLimit).filter(models.ChefBotLimit.date < cutoff).delete()
                session.query(models.FoodSuggestLimit).filter(models.FoodSuggestLimit.date < cutoff).delete()
                session.query(models.CaloriePhotoLimit).filter(models.CaloriePhotoLimit.date < cutoff).delete()
                session.commit()
        except Exception as e:
            print(f"Limit cleanup error: {e}")
        time.sleep(86400)

cleanup_thread = threading.Thread(target=cleanup_old_limits, daemon=True)
cleanup_thread.start()

@app.head("/")
def head_index():
    return Response(status_code=200)

# Pydantic models for request/response validation
class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = ""
    email: Optional[str] = ""
    goal: Optional[str] = ""  # "kilo_alma" or "kilo_verme"
    daily_calorie_goal: Optional[int] = None

class RecipeRequest(BaseModel):
    food_name: str
    is_diet: bool = False

class ProfileUpdate(BaseModel):
    daily_calorie_goal: Optional[int] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class RecipeResponse(BaseModel):
    id: int
    name: str
    ingredients: Optional[List[str]] = []
    steps: Optional[List[str]] = []
    calories: Optional[str] = None
    is_diet: bool = False
    created_at: Optional[datetime] = None
    xp: Optional[int] = None
    level: Optional[int] = None
    streak: Optional[int] = None
    daily_calorie_goal: Optional[int] = None

    class Config:
        from_attributes = True  # Pydantic v2
        orm_mode = True  # Pydantic v1 fallback

def get_turkey_date():
    # Turkey is UTC+3
    turkey_time = datetime.utcnow() + timedelta(hours=3)
    return turkey_time.date()

@app.post("/api/register", response_model=Token)
@limiter.limit("5/minute")
def register(request: Request, user: UserCreate, session: Session = Depends(db.get_db)):
    db_user = session.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Kullanıcı adı zaten alınmış.")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        password_hash=hashed_password,
        full_name=user.full_name or None,
        email=user.email or None,
        goal=user.goal or None,
        daily_calorie_goal=user.daily_calorie_goal
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    access_token = auth.create_access_token(data={"sub": new_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

def check_and_update_streak(user):
    today = get_turkey_date()
    if user.last_recipe_date is None:
        return
    days_missed = (today - user.last_recipe_date).days - 1
    if days_missed > 0:
        user.streak = 0

@app.post("/api/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(db.get_db)):
    user = session.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Hatalı kullanıcı adı veya şifre.")
    check_and_update_streak(user)
    session.commit()
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/user/me")
def get_user_me(auth_data: tuple = Depends(auth.get_current_user_with_db)):
    current_user, session = auth_data
    check_and_update_streak(current_user)
    return {
        "username": current_user.username,
        "is_plus": bool(current_user.is_plus),
        "xp": current_user.xp or 0,
        "level": current_user.level or 1,
        "streak": current_user.streak or 0,
        "full_name": current_user.full_name or "",
        "email": current_user.email or "",
        "goal": current_user.goal or "",
        "daily_calorie_goal": current_user.daily_calorie_goal
    }

@app.put("/api/user/profile")
def update_profile(update: ProfileUpdate, auth_data: tuple = Depends(auth.get_current_user_with_db)):
    current_user, session = auth_data
    if update.daily_calorie_goal is not None:
        current_user.daily_calorie_goal = update.daily_calorie_goal
    session.commit()
    return {"ok": True, "daily_calorie_goal": current_user.daily_calorie_goal}

@app.post("/api/recipe/generate", response_model=RecipeResponse)
@limiter.limit("20/minute")
def generate_new_recipe(request: Request, req: RecipeRequest, auth_data: tuple = Depends(auth.get_current_user_with_db)):
    current_user, session = auth_data
    today = get_turkey_date()
    
    # Check limit (free: 2, plus: 20)
    daily_limit = 20 if current_user.is_plus else 2
    limit_record = session.query(models.UsageLimit).filter(
        models.UsageLimit.user_id == current_user.id,
        models.UsageLimit.date == today
    ).first()
    
    if limit_record and limit_record.count >= daily_limit:
        raise HTTPException(status_code=429, detail=f"Günlük tarif oluşturma limitine ({daily_limit}) ulaştınız. Yarın tekrar deneyin.")

    
    # Generate recipe
    recipe_data = ai.generate_recipe(req.food_name, req.is_diet)
    if not recipe_data:
        raise HTTPException(status_code=500, detail="Tarif oluşturulurken bir hata oluştu. Lütfen tekrar deneyin.")
    
    # Update limit (no recipe saved to DB)
    if limit_record:
        limit_record.count += 1
    else:
        new_limit = models.UsageLimit(user_id=current_user.id, date=today, count=1)
        session.add(new_limit)
        
    # XP ve seri güncelle
    xp_gain = 20 if req.is_diet else 10
    current_user.xp = (current_user.xp or 0) + xp_gain
    current_user.level = ((current_user.xp) // 100) + 1

    check_and_update_streak(current_user)
    if current_user.last_recipe_date != today:
        current_user.streak = (current_user.streak or 0) + 1
        current_user.last_recipe_date = today

    session.commit()

    return RecipeResponse(
        id=0,
        name=recipe_data.get("name", req.food_name),
        ingredients=recipe_data.get("ingredients", []),
        steps=recipe_data.get("steps", []),
        calories=recipe_data.get("estimated_calories", "Bilinmiyor"),
        is_diet=req.is_diet,
        created_at=datetime.utcnow(),
        xp=current_user.xp,
        level=current_user.level,
        streak=current_user.streak,
        daily_calorie_goal=current_user.daily_calorie_goal
    )

@app.get("/api/recipe/history", response_model=List[RecipeResponse])
def get_history(current_user: models.User = Depends(auth.get_current_user)):
    return []


# ── Kalori Pydantic modelleri ────────────────────────────────────────────────

class CalorieLogRequest(BaseModel):
    bmr: float
    active_calories: float
    intake_calories: float

class CalorieLogResponse(BaseModel):
    id: int
    date: str
    bmr: float
    active_calories: float
    intake_calories: float
    deficit: float
    xp: Optional[int] = None
    level: Optional[int] = None
    streak: Optional[int] = None
    daily_calorie_goal: Optional[int] = None

    class Config:
        from_attributes = True
        orm_mode = True

# ── Kalori log endpoint'leri ─────────────────────────────────────────────────

@app.post("/api/calorie/log", response_model=CalorieLogResponse)
def save_calorie_log(req: CalorieLogRequest, auth_data: tuple = Depends(auth.get_current_user_with_db)):
    current_user, session = auth_data
    bmr = round(req.bmr, 2)
    deficit = round((bmr + req.active_calories) - req.intake_calories, 2)
    today = get_turkey_date()

    # Calorie logs are now client-side (localStorage), only update streak
    check_and_update_streak(current_user)
    if current_user.last_recipe_date != today:
        current_user.streak = (current_user.streak or 0) + 1
        current_user.last_recipe_date = today

    session.commit()

    return CalorieLogResponse(
        id=0,
        date=str(today),
        bmr=bmr,
        active_calories=req.active_calories,
        intake_calories=req.intake_calories,
        deficit=deficit,
        xp=current_user.xp,
        level=current_user.level,
        streak=current_user.streak,
        daily_calorie_goal=current_user.daily_calorie_goal
    )

@app.get("/api/calorie/log", response_model=List[CalorieLogResponse])
def get_calorie_logs(current_user: models.User = Depends(auth.get_current_user)):
    return []

# ── ChefBot ──────────────────────────────────────────────────────────────────

CHEFBOT_SYSTEM_PROMPT = """You are ChefBot, an expert dietitian and culinary advisor integrated into the Mr.Food app. Your sole purposes are:
1. Estimating calorie counts of foods and meals (by portion, weight, or description)
2. Giving dietary advice, healthy eating tips, and meal recommendations
3. Answering nutrition-related questions

STRICT RULES — never break these:
- You NEVER provide recipe instructions, ingredient lists, or cooking steps. If the user asks for a recipe, firmly decline and redirect: suggest they use the "Oluştur" tab in the app for recipes.
- You only discuss food in the context of nutrition, calories, and dietary advice.
- Always respond in Turkish, regardless of the language the user writes in.
- Be friendly, concise, and professional like a real dietitian.
- When estimating calories, always clarify that these are approximate values."""

class ChefBotMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str

class ChefBotRequest(BaseModel):
    messages: List[ChefBotMessage]

@app.post("/api/chefbot")
@limiter.limit("30/minute")
def chefbot(request: Request, req: ChefBotRequest, auth_data: tuple = Depends(auth.get_current_user_with_db)):
    current_user, session = auth_data
    today = get_turkey_date()

    # Check chefbot limit (free: 5, plus: 50)
    chefbot_limit = 50 if current_user.is_plus else 5
    limit = session.query(models.ChefBotLimit).filter(
        models.ChefBotLimit.user_id == current_user.id,
        models.ChefBotLimit.date == today
    ).first()
    if limit and limit.count >= chefbot_limit:
        raise HTTPException(status_code=429, detail=f"Günlük ChefBot mesaj limitine ({chefbot_limit}) ulaştınız. Yarın tekrar deneyin.")

    # Gemini'ye gönder
    try:
        contents = []
        for m in req.messages:
            role = "user" if m.role == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m.content)]))
        response = chefbot_client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=CHEFBOT_SYSTEM_PROMPT,
                temperature=0.6,
                max_output_tokens=512
            )
        )
        reply = response.text
    except Exception as e:
        print(f"ChefBot Gemini hatası: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"ChefBot şu an yanıt veremiyor: {str(e)}")

    # Limit güncelle
    if limit:
        limit.count += 1
    else:
        session.add(models.ChefBotLimit(user_id=current_user.id, date=today, count=1))

    # ChefBot XP
    current_user.xp = (current_user.xp or 0) + 10
    current_user.level = ((current_user.xp) // 100) + 1

    # Streak güncelle (kalori kayıt gibi)
    check_and_update_streak(current_user)
    if current_user.last_recipe_date != today:
        current_user.streak = (current_user.streak or 0) + 1
        current_user.last_recipe_date = today

    session.commit()

    return {
        "reply": reply,
        "xp": current_user.xp,
        "level": current_user.level,
        "streak": current_user.streak,
        "daily_calorie_goal": current_user.daily_calorie_goal
    }

@app.get("/api/chefbot/limit")
def get_chefbot_limit(auth_data: tuple = Depends(auth.get_current_user_with_db)):
    current_user, session = auth_data
    today = get_turkey_date()
    chefbot_limit = 50 if current_user.is_plus else 5
    limit = session.query(models.ChefBotLimit).filter(
        models.ChefBotLimit.user_id == current_user.id,
        models.ChefBotLimit.date == today
    ).first()
    used = limit.count if limit else 0
    return {"used": used, "limit": chefbot_limit, "is_plus": current_user.is_plus}

# ── Bana Yemek Öner ──────────────────────────────────────────────────────────

class FoodSuggestResponse(BaseModel):
    id: int
    food_name: str
    is_diet: bool
    used: int
    limit: int
    xp: Optional[int] = None
    level: Optional[int] = None
    streak: Optional[int] = None
    daily_calorie_goal: Optional[int] = None

    class Config:
        from_attributes = True
        orm_mode = True

@app.get("/api/food-suggest/limit")
def get_food_suggest_limit(auth_data: tuple = Depends(auth.get_current_user_with_db)):
    current_user, session = auth_data
    today = get_turkey_date()
    daily_limit = 20 if current_user.is_plus else 2
    limit_record = session.query(models.FoodSuggestLimit).filter(
        models.FoodSuggestLimit.user_id == current_user.id,
        models.FoodSuggestLimit.date == today
    ).first()
    used = limit_record.count if limit_record else 0
    return {"used": used, "limit": daily_limit, "is_plus": current_user.is_plus}

@app.get("/api/food-suggest", response_model=FoodSuggestResponse)
def suggest_random_food(is_diet: str = "false", auth_data: tuple = Depends(auth.get_current_user_with_db)):
    current_user, session = auth_data
    today = get_turkey_date()
    daily_limit = 20 if current_user.is_plus else 2
    diet_filter = is_diet.lower() == "true"

    limit_record = session.query(models.FoodSuggestLimit).filter(
        models.FoodSuggestLimit.user_id == current_user.id,
        models.FoodSuggestLimit.date == today
    ).first()

    used = limit_record.count if limit_record else 0

    if used >= daily_limit:
        raise HTTPException(status_code=429, detail=f"Günlük yemek önerisi limitine ({daily_limit}) ulaştınız. Yarın tekrar deneyin.")

    total = session.query(func.count(models.FoodCard.id)).filter(models.FoodCard.is_diet == diet_filter).scalar()
    if not total:
        raise HTTPException(status_code=404, detail="Veritabanında yemek kaydı bulunamadı.")
    food = session.query(models.FoodCard).filter(models.FoodCard.is_diet == diet_filter).offset(random.randint(0, total - 1)).limit(1).first()
    if not food:
        raise HTTPException(status_code=404, detail="Veritabanında yemek kaydı bulunamadı.")

    if limit_record:
        limit_record.count += 1
    else:
        session.add(models.FoodSuggestLimit(user_id=current_user.id, date=today, count=1))

    # 5 XP kazan
    current_user.xp = (current_user.xp or 0) + 5
    current_user.level = ((current_user.xp) // 100) + 1

    session.commit()

    return FoodSuggestResponse(
        id=food.id,
        food_name=food.food_name,
        is_diet=food.is_diet,
        used=used + 1,
        limit=daily_limit,
        xp=current_user.xp,
        level=current_user.level,
        streak=current_user.streak,
        daily_calorie_goal=current_user.daily_calorie_goal
    )

# ── Fotoğrafla Kalori Ölçer ───────────────────────────────────────────────────

class CaloriePhotoRequest(BaseModel):
    image: str  # base64 encoded image
    details: Optional[str] = ""

class CaloriePhotoResponse(BaseModel):
    food_name: Optional[str] = None
    total_calories: Optional[str] = None
    protein: Optional[str] = None
    carbs: Optional[str] = None
    fat: Optional[str] = None
    portion_size: Optional[str] = None
    description: Optional[str] = None
    error: Optional[str] = None
    used: int = 0
    limit: int = 1
    xp: Optional[int] = None
    level: Optional[int] = None
    streak: Optional[int] = None
    daily_calorie_goal: Optional[int] = None

    class Config:
        from_attributes = True
        orm_mode = True

@app.post("/api/calorie-photo/analyze")
@limiter.limit("10/minute")
def analyze_calorie_photo(request: Request, req: CaloriePhotoRequest, auth_data: tuple = Depends(auth.get_current_user_with_db)):
    current_user, session = auth_data
    today = get_turkey_date()
    daily_limit = 10 if current_user.is_plus else 1

    limit_record = session.query(models.CaloriePhotoLimit).filter(
        models.CaloriePhotoLimit.user_id == current_user.id,
        models.CaloriePhotoLimit.date == today
    ).first()

    used = limit_record.count if limit_record else 0
    if used >= daily_limit:
        raise HTTPException(status_code=429, detail=f"Günlük kalori analizi limitine ({daily_limit}) ulaştınız. {'Plus üyeliğinizle 10 kez analiz yapabilirsiniz.' if current_user.is_plus else 'Plus üyeliğe yükselterek 10 kez analiz yapabilirsiniz.'}")

    result = ai.analyze_food_photo(req.image, req.details or "")
    if not result:
        raise HTTPException(status_code=500, detail="Fotoğraf analiz edilirken bir hata oluştu. Lütfen tekrar deneyin.")

    if result.get("error"):
        return CaloriePhotoResponse(error=result["error"], used=used, limit=daily_limit)

    if limit_record:
        limit_record.count += 1
    else:
        session.add(models.CaloriePhotoLimit(user_id=current_user.id, date=today, count=1))

    # XP kazandır
    current_user.xp = (current_user.xp or 0) + 15
    current_user.level = ((current_user.xp) // 100) + 1

    # Streak güncelle
    check_and_update_streak(current_user)
    if current_user.last_recipe_date != today:
        current_user.streak = (current_user.streak or 0) + 1
        current_user.last_recipe_date = today

    session.commit()

    return CaloriePhotoResponse(
        food_name=result.get("food_name"),
        total_calories=result.get("total_calories"),
        protein=result.get("protein"),
        carbs=result.get("carbs"),
        fat=result.get("fat"),
        portion_size=result.get("portion_size"),
        description=result.get("description"),
        used=used + 1,
        limit=daily_limit,
        xp=current_user.xp,
        level=current_user.level,
        streak=current_user.streak,
        daily_calorie_goal=current_user.daily_calorie_goal
    )

@app.get("/api/calorie-photo/limit")
def get_calorie_photo_limit(auth_data: tuple = Depends(auth.get_current_user_with_db)):
    current_user, session = auth_data
    today = get_turkey_date()
    daily_limit = 10 if current_user.is_plus else 1
    limit_record = session.query(models.CaloriePhotoLimit).filter(
        models.CaloriePhotoLimit.user_id == current_user.id,
        models.CaloriePhotoLimit.date == today
    ).first()
    used = limit_record.count if limit_record else 0
    return {"used": used, "limit": daily_limit, "is_plus": current_user.is_plus}

# ── Lider Tablosu ────────────────────────────────────────────────────────────

class LeaderboardUser(BaseModel):
    rank: int
    username: str
    xp: int
    level: int

    class Config:
        from_attributes = True
        orm_mode = True

class LeaderboardResponse(BaseModel):
    top_30: List[LeaderboardUser]
    current_user: LeaderboardUser
    total_users: int
    in_top_30: bool

@app.get("/api/leaderboard")
def get_leaderboard(auth_data: tuple = Depends(auth.get_current_user_with_db)):
    current_user, session = auth_data

    top_users = session.query(models.User).order_by(models.User.xp.desc()).limit(30).all()
    top_30_data = []
    for i, u in enumerate(top_users):
        top_30_data.append(LeaderboardUser(rank=i+1, username=u.username, xp=u.xp or 0, level=u.level or 1))

    user_rank = session.query(func.count(models.User.id)).filter(
        models.User.xp > current_user.xp
    ).scalar() + 1

    total_users = session.query(func.count(models.User.id)).scalar()
    in_top_30 = user_rank <= 30

    return LeaderboardResponse(
        top_30=top_30_data,
        current_user=LeaderboardUser(rank=user_rank, username=current_user.username, xp=current_user.xp or 0, level=current_user.level or 1),
        total_users=total_users,
        in_top_30=in_top_30
    )



# ── Promosyon Kodu ────────────────────────────────────────────────────────────

class PromoRedeemRequest(BaseModel):
    code: str

class PromoRedeemResponse(BaseModel):
    ok: bool
    message: str
    reward_type: Optional[str] = None
    reward_value: Optional[int] = None
    xp: Optional[int] = None
    level: Optional[int] = None
    streak: Optional[int] = None
    daily_calorie_goal: Optional[int] = None

@app.post("/api/promo/redeem")
def redeem_promo(req: PromoRedeemRequest, auth_data: tuple = Depends(auth.get_current_user_with_db)):
    current_user, session = auth_data
    code = req.code.strip().upper()

    promo = session.query(models.PromoCode).filter(models.PromoCode.code == code).first()
    if not promo:
        return PromoRedeemResponse(ok=False, message="Geçersiz promosyon kodu.")
    if not promo.is_active:
        return PromoRedeemResponse(ok=False, message="Bu kodun geçerliliği sona ermiştir.")
    if promo.remaining_uses <= 0:
        return PromoRedeemResponse(ok=False, message="Bu kodun geçerliliği sona ermiştir.")

    already_used = session.query(models.RedeemedCode).filter(
        models.RedeemedCode.user_id == current_user.id,
        models.RedeemedCode.promo_code_id == promo.id
    ).first()
    if already_used:
        return PromoRedeemResponse(ok=False, message="Bu kodu daha önce kullanmışsınız.")

    if promo.reward_type == "xp":
        current_user.xp = (current_user.xp or 0) + promo.reward_value
        current_user.level = ((current_user.xp) // 100) + 1
        promo.remaining_uses -= 1
        session.add(models.RedeemedCode(user_id=current_user.id, promo_code_id=promo.id))
        session.commit()
        return PromoRedeemResponse(
            ok=True,
            message=f"Tebrikler! {promo.reward_value} XP kazandınız!",
            reward_type="xp",
            reward_value=promo.reward_value,
            xp=current_user.xp,
            level=current_user.level,
            streak=current_user.streak,
            daily_calorie_goal=current_user.daily_calorie_goal
        )

    elif promo.reward_type == "limit_reset":
        today = get_turkey_date()
        for limit_model in [models.UsageLimit, models.ChefBotLimit, models.FoodSuggestLimit, models.CaloriePhotoLimit]:
            record = session.query(limit_model).filter(
                limit_model.user_id == current_user.id,
                limit_model.date == today
            ).first()
            if record:
                session.delete(record)
        promo.remaining_uses -= 1
        session.add(models.RedeemedCode(user_id=current_user.id, promo_code_id=promo.id))
        session.commit()
        return PromoRedeemResponse(
            ok=True,
            message="Tebrikler! Günlük limitleriniz sıfırlandı!",
            reward_type="limit_reset",
            reward_value=0,
            xp=current_user.xp,
            level=current_user.level,
            streak=current_user.streak,
            daily_calorie_goal=current_user.daily_calorie_goal
        )

    return PromoRedeemResponse(ok=False, message="Bu kodun ödül tipi tanımsız.")

# ── Static dosyalar ──────────────────────────────────────────────────────────

@app.get("/")
def serve_index():
    return FileResponse("index.html")

@app.get("/sw.js")
def serve_sw():
    return FileResponse("sw.js")

@app.get("/manifest.json")
def serve_manifest():
    return FileResponse("manifest.json")

@app.get("/logo.png")
def serve_logo():
    return FileResponse("logo.png", media_type="image/png")
