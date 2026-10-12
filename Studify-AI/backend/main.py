from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .database import engine, Base, init_db
from .routes import auth_routes, flashcard_routes, solver_routes, summary_routes, quiz_routes, coach_routes, profile_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama başlarken tabloları oluştur
    await init_db()
    yield
    # Uygulama kapanırken bağlantıları temizle
    await engine.dispose()

app = FastAPI(title="Studify API", lifespan=lifespan)

# CORS Ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Rotaları
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Auth"])
app.include_router(flashcard_routes.router, prefix="/api/flashcards", tags=["Flashcards"])
app.include_router(solver_routes.router, prefix="/api/solver", tags=["Solver"])
app.include_router(summary_routes.router, prefix="/api/summary", tags=["Summary"])
app.include_router(quiz_routes.router, prefix="/api/quiz", tags=["Quiz"])
app.include_router(coach_routes.router, prefix="/api/coach", tags=["Coach"])
app.include_router(profile_routes.router, prefix="/api/profile", tags=["Profile"])

@app.get("/api/health")
@app.head("/api/health")
async def health_check():
    return {"status": "ok", "app": "Studify"}

# Frontend static files mount
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
