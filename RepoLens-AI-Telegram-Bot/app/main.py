from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.telegram.bot import setup_bot
from app.logger import logger
import asyncio

# Create bot application instance
bot_app = setup_bot()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run the Telegram Bot polling asynchronously alongside FastAPI
    logger.info("Starting Telegram Bot via Polling...")
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    yield
    # Shutdown
    logger.info("Stopping Telegram Bot...")
    await bot_app.updater.stop()
    await bot_app.stop()
    await bot_app.shutdown()

app = FastAPI(
    title="RepoLens Bot",
    description="MVP Telegram bot that analyzes GitHub repositories using Gemini 3.1 Flash Lite",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "RepoLens Bot is running."}
