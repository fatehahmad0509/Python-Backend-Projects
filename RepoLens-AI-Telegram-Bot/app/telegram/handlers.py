import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.logger import logger
from app.services.github import GitHubService
from app.services.gemini import GeminiService
from app.models.schemas import AnalysisReport

github_service = GitHubService()
gemini_service = GeminiService()

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Welcome to RepoLens Bot! 🔍\n\n"
        "Send me a GitHub repository URL, and I'll generate a detailed AI-powered technical report.\n"
        "Example: https://github.com/tiangolo/fastapi"
    )
    await update.message.reply_text(welcome_text)

async def url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # Simple regex to extract owner and repo
    match = re.search(r"https?://github\.com/([\w-]+)/([\w.-]+)", text)
    if not match:
        await update.message.reply_text("Please send a valid GitHub repository URL.")
        return
        
    owner, repo = match.groups()
    
    # Store repo info in user_data for the callback
    context.user_data["owner"] = owner
    context.user_data["repo"] = repo
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data="readme_yes"),
            InlineKeyboardButton("❌ No", callback_data="readme_no")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Target: {owner}/{repo}\n\nInclude README analysis?",
        reply_markup=reply_markup
    )

def format_report(report: AnalysisReport) -> str:
    msg = f"📊 *RepoLens Analysis Report*\n\n"
    msg += f"📝 *Summary:*\n{report.summary}\n\n"
    msg += f"🛠 *Technologies:*\n{', '.join(report.technologies)}\n\n"
    msg += f"🏗 *Code Quality:*\n{report.code_quality}\n\n"
    msg += f"⚠️ *Issues / Bad Practices:*\n"
    for issue in report.issues:
        msg += f"- {issue}\n"
    msg += f"\n🧑‍💻 *Estimated Developer Level:* {report.developer_level}\n\n"
    msg += f"💡 *Improvement Suggestions:*\n"
    for suggestion in report.suggestions:
        msg += f"- {suggestion}\n"
    return msg

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    owner = context.user_data.get("owner")
    repo = context.user_data.get("repo")
    
    if not owner or not repo:
        await query.edit_message_text("Session expired. Please send the URL again.")
        return
        
    include_readme = query.data == "readme_yes"
    
    await query.edit_message_text(f"🔍 Analyzing {owner}/{repo}... (This might take a few moments)")
    
    # Fetch Data
    repo_data = await github_service.fetch_repository_data(owner, repo, include_readme)
    
    if not repo_data:
        await query.edit_message_text("❌ Failed to fetch repository data. Please check the URL or try again later.")
        return
        
    # Run AI Analysis
    report = await gemini_service.analyze_repository(repo_data, owner, repo)
    
    if isinstance(report, str):
        # Fallback error string
        await query.edit_message_text(f"❌ Analysis failed: {report}")
        return
        
    # Format and Send
    try:
        formatted_message = format_report(report)
        # Telegram max message length is 4096. Truncate if necessary.
        if len(formatted_message) > 4000:
            formatted_message = formatted_message[:4000] + "\n\n[Message Truncated]"
        
        await query.edit_message_text(formatted_message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Failed to send formatted report: {e}")
        await query.edit_message_text("❌ Failed to format and send the report.")
        
    # Clean up context
    context.user_data.pop("owner", None)
    context.user_data.pop("repo", None)
