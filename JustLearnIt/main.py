from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.db import init_db, get_conn
from modules import students, analytics, teacher, auth, questions, match, market, admin
from datetime import datetime
import pytz

# Initialize the FastAPI application
app = FastAPI(title="JustLearnIt API", version="2.0.0")

# Allow all origins for CORS (configure more restrictively in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all module routers
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(analytics.router)
app.include_router(teacher.router)
app.include_router(questions.router)
app.include_router(match.router)
app.include_router(market.router)
app.include_router(admin.router)


@app.on_event("startup")
def startup():
    """Initialize the database on application startup."""
    init_db()


@app.get("/health")
def health():
    """Health check endpoint to verify the API is running."""
    return {"status": "ok", "app": "JustLearnIt", "version": "2.0.0"}


@app.get("/debug/time")
def debug_time():
    """Debug endpoint returning current time in UTC, Turkey timezone, and from the database."""
    tr = pytz.timezone("Europe/Istanbul")
    now_tr = datetime.now(tr)
    now_utc = datetime.now(pytz.utc)
    with get_conn() as (conn, c):
        c.execute("SELECT NOW()")
        db_now = c.fetchone()[0]
    return {
        "python_utc": now_utc.isoformat(),
        "python_turkey": now_tr.isoformat(),
        "db_now": db_now.isoformat()
    }
