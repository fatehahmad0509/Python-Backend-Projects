
# Application entry point - FastAPI server for CookieLearn
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from database import Base, engine
from routers import admin, ai, auth, languages, leaderboard, practice, progress, stats, users
from seed import seed_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("cookielearn")

app = FastAPI(title="CookieLearn API", version="1.0.0")

# Allow cross-origin requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded avatars and static assets
STATIC_DIR = ROOT_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def on_startup():
    # Create database tables and populate seed data on first run
    logger.info("Creating tables + seeding...")
    Base.metadata.create_all(bind=engine)
    try:
        seed_all()
        logger.info("Seed complete.")
    except Exception as e:
        logger.exception("Seed failed: %s", e)


from fastapi import APIRouter
api = APIRouter(prefix="/api")

@api.get("/")
def root():
    return {"name": "CookieLearn API", "version": "1.0.0"}

@api.get("/health")
@api.head("/health")
def health():
    return {"status": "ok"}


# Register all feature routers under the /api prefix
api.include_router(auth.router)
api.include_router(users.router)
api.include_router(languages.router)
api.include_router(progress.router)
api.include_router(practice.router)
api.include_router(stats.router)
api.include_router(leaderboard.router)
api.include_router(ai.router)
api.include_router(admin.router)

app.include_router(api)
