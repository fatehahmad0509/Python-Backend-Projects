import re
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from app.config import settings
from app.telegram.handlers import start_handler, url_handler, callback_handler

def setup_bot() -> Application:
    """Initialize and configure the Telegram Bot Application."""
    if not settings.telegram_bot_token or settings.telegram_bot_token == "your_telegram_bot_token_here":
        raise ValueError("TELEGRAM_BOT_TOKEN is not set properly in the environment.")
        
    application = Application.builder().token(settings.telegram_bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_handler))
    
    # Listen for GitHub URLs specifically
    github_url_filter = filters.Regex(re.compile(r"https?://github\.com/[\w-]+/[\w.-]+"))
    application.add_handler(MessageHandler(filters.TEXT & github_url_filter, url_handler))
    
    # Callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    return application
