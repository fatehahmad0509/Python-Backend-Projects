# Mr.Food v2 — AI-Powered Nutrition Assistant

Mr.Food is a web application that uses artificial intelligence for recipe generation, calorie analysis from photos, nutrition tracking, and a ChefBot chat assistant. It runs on a FastAPI backend with PostgreSQL and a vanilla HTML/CSS/JS frontend.

## Features

| Tab | Description |
|---|---|
| **Home** | User dashboard with daily calorie summary |
| **Create** | AI recipe generation via Gemini 3.1 Flash Lite (free: 2/day, Plus: 20/day) |
| **History** | Past recipe history (stored in localStorage) |
| **Calorie** | Daily calorie tracking, BMR/activity calculation, cumulative food entry |
| **ChefBot** | Gemini 3.1 Flash Lite nutrition advisor chat (free: 5/day, Plus: 50/day) |
| **Suggest** | Random food suggestion (free: 2/day, Plus: 20/day) |
| **Calorie Cam** | AI-powered calorie analysis from photos (free: 1/day, Plus: 10/day) |
| **Leaderboard** | Top 30 users by XP |
| **Profile** | User info, Plus membership, XP/Level/Streak, Promosyon Kodu kullanma |

### XP & Level System

- Recipe (normal): **10 XP**
- Recipe (diet): **20 XP**
- ChefBot message: **10 XP**
- Food suggestion: **5 XP**
- Calorie photo analysis: **15 XP**
- Every **100 XP** = 1 level up

## Tech Stack

- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL (SQLAlchemy ORM)
- **AI (Recipe & Photo):** Google Gemini 3.1 Flash Lite
- **AI (ChefBot):** Google Gemini 3.1 Flash Lite
- **Auth:** JWT (python-jose) + bcrypt (passlib)
- **Rate Limiting:** SlowAPI
- **Frontend:** Vanilla HTML/CSS/JS, Phosphor Icons, Inter Font

## What's New in v2

### New Features

- **Calorie Cam (Photo Analysis)** — Upload a food photo and get calorie, protein, carb, and fat analysis via Gemini AI
- **Leaderboard** — Top 30 users ranked by XP, with current user's rank shown even if outside top 30
- **Cumulative Food Entry** — Daily food entries tracked via localStorage (deleted after each day)
- **Date Selection for Calorie Log** — When logging daily calorie deficit, today's date is used by default; a different date can be selected for backlogging
- **Add from Photo Analysis** — The "Add to Today's Consumption" button in the Calorie Cam result allows saving AI-detected calories and food name to the daily food entry list in one click
- **Startup Env Validation** — Required environment variables (DATABASE_URL, JWT_SECRET, GEMINI_API_KEY) are checked on startup; the app exits with an error if any are missing
- **Enhanced Registration** — Full name, email, goal (weight gain/loss), daily calorie goal

### Changes Summary

| Change | Description |
|---|---|
| Plus section | Moved from bottom nav to Profile page |
| Bottom nav | Font reduced to 8px, overflow text uses ellipsis to fit 9 buttons |
| Recipe history | **Moved from server DB to localStorage** — reduces database load |
| Calorie log history | **Moved from server DB to localStorage** — only streak updates remain server-side |
| Unused models | `Recipe`, `CalorieLog`, `UserProfile` deleted to prevent `create_all()` from recreating dropped tables |
| Startup migration | Added `full_name`, `email`, `goal`, `daily_calorie_goal` columns to `users` table; added compound indexes on `(user_id, date)` for all limit tables |
| applyPlusUI | Fixed limit resetting for free users on login |
| Add from Photo Analysis | Photo analysis result card now has an "Add to Today's Consumption" button to save AI results as a food entry |
| Button loading state | The add button shows a spinner + "Adding..." while processing, then changes to "Added!" on success |
| Limit default display | Limit counters show `-` instead of `0` while waiting for the API response |
| Leaderboard optimization | **Removed full table scan** — rank calculation now uses COUNT subquery instead of loading all users into memory |
| Dual session fix | **Single DB session per request** — `get_current_user_with_db` combined dependency eliminates redundant connection pool usage |
| Limit table cleanup | **3-day TTL** — background thread runs daily to delete limit records (`usage_limits`, `chefbot_limits`, `food_suggest_limits`, `calorie_photo_limits`) older than 3 days |
| `get_turkey_date()` dedup | **Duplicate calls removed** from `generate_new_recipe` and `chefbot` endpoints — single call reused |
| `check_and_update_streak` | **Removed early `session.commit()`** — all changes flush together in the endpoint's final commit |
| Login bug fix | `check_and_update_streak` login'de 2 argümanla çağrılıp crash atıyormuş, düzeltildi; eksik `session.commit()` eklendi |
| `func.random()` → random offset | **Yemek önerme sorgusu optimize edildi** — tüm satırları sıralamak yerine COUNT + random OFFSET |
| Write endpoints return user stats | **Recipe, ChefBot, CalorieLog, FoodSuggest, CaloriePhoto** artık `xp/level/streak` döndürüyor, frontend ekstra API çağrısı yapmıyor |
| Profile calorie goal edit | **`PUT /api/user/profile`** — users can now update their daily calorie goal from the Profile page |
| Promosyon Kodu | **`POST /api/promo/redeem`** — kullanıcılar profil sayfasından kod girerek XP veya limit sıfırlama ödülü kazanabilir. Kodlar `promo_codes` tablosunda tanımlanır, `remaining_uses` adet kullanıma sahiptir |
| Food entries → localStorage | **Food entries moved to client-side localStorage** — daily food entries are stored on-device and cleaned up when a new day starts. Backend `food_entries` tablosu ve endpoint'leri kaldırıldı |

### Database Schema

Tables: `users`, `usage_limits`, `chefbot_limits`, `food_cards`, `food_suggest_limits`, `calorie_photo_limits`, `promo_codes`, `redeemed_codes`

The `goal` field stores English values: `weight_gain` or `weight_loss`.

## Setup

```bash
git clone https://github.com/fatehahmad0509/Mr-Food.git
cd Mr-Food
pip install -r requirements.txt
```

Required environment variables:

```
DATABASE_URL=postgresql://...
JWT_SECRET=...
GEMINI_API_KEY=...
GEMINI_CHEFBOT_API_KEY=   # optional — falls back to GEMINI_API_KEY
```

```bash
uvicorn main:app --reload
```

## Deploy (Render)

1. Create a new **Web Service** on Render
2. Start Command: `uvicorn main:app --host 0.0.0.0 --port 10000`
3. Set environment variables as listed above
4. No build command needed (requirements.txt is auto-detected)

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/register` | Register a new user |
| POST | `/api/login` | Log in |
| GET | `/api/user/me` | Get current user info |
| PUT | `/api/user/profile` | Update profile (daily_calorie_goal) |
| POST | `/api/recipe/generate` | Generate an AI recipe |
| GET | `/api/recipe/history` | Get recipe history (returns empty, client-side) |
| POST | `/api/calorie/log` | Log calories (streak only) |
| GET | `/api/calorie/log` | Get calorie log history (returns empty, client-side) |
| POST | `/api/chefbot` | Send a ChefBot message |
| GET | `/api/chefbot/limit` | Get ChefBot usage limit |
| GET | `/api/food-suggest` | Get a random food suggestion |
| GET | `/api/food-suggest/limit` | Get food suggestion usage limit |
| POST | `/api/calorie-photo/analyze` | Analyze food photo for calories |
| GET | `/api/calorie-photo/limit` | Get calorie photo usage limit |
| GET | `/api/leaderboard` | Get leaderboard |
| POST | `/api/promo/redeem` | Redeem a promo code (XP or limit reset) |

---

*Mr.Food v2 — 2026*
