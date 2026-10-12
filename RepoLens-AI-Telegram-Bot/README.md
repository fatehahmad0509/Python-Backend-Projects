# 🔍 RepoLens Bot

A Telegram bot that analyzes GitHub repositories using Google Gemini AI and delivers detailed technical reports — straight to your chat.

---

## Features

- **GitHub Repository Analysis** — Fetches the full file tree of any public (or private, with a token) GitHub repository
- **README Parsing** — Optionally includes README.md content for richer context
- **AI-Powered Reports** — Uses Gemini to generate structured technical insights
- **Inline Keyboard UX** — Clean Telegram inline buttons for a smooth user experience
- **FastAPI Backend** — Lightweight HTTP server with a health-check endpoint, running alongside the bot via async polling

---

## Tech Stack

| Layer | Technology |
|---|---|
| Bot Framework | python-telegram-bot 21.2 |
| AI Model | Google Gemini (gemini-3.1-flash-lite) |
| Web Framework | FastAPI + Uvicorn |
| GitHub API Client | httpx |
| Data Validation | Pydantic v2 |
| Config Management | pydantic-settings |

---

## Project Structure

```
app/
├── main.py              # FastAPI app entry point with bot lifecycle
├── config.py            # Settings loaded from .env
├── logger.py            # Centralized logging config
├── models/
│   ├── __init__.py
│   └── schemas.py       # Pydantic models (RepoData, AnalysisReport, etc.)
├── services/
│   ├── __init__.py
│   ├── github.py        # GitHub API integration
│   └── gemini.py        # Gemini AI integration
└── telegram/
    ├── __init__.py
    ├── bot.py           # Bot setup and handler registration
    └── handlers.py      # Command, message, and callback handlers
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/repolens-bot.git
cd repolens-bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_TOKEN=your_github_token_here   # Required for private repos
PYTHON_VERSION=3.10.0
```

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ Yes | Get from [@BotFather](https://t.me/BotFather) |
| `GEMINI_API_KEY` | ✅ Yes | Get from [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | ⚠️ Optional | Required to analyze private repositories and avoid rate limits |
| `PYTHON_VERSION` | ✅ Yes | Must be `3.10.0` |

### 4. Run the application

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The FastAPI server starts and the Telegram bot begins polling automatically.

---

## Usage

1. Open your bot on Telegram and send `/start`
2. Send any GitHub repository URL, for example:
   ```
   https://github.com/tiangolo/fastapi
   ```
3. Choose whether to include the README in the analysis
4. Wait a few seconds while the bot fetches repo data and runs the AI analysis
5. Receive a detailed technical report including:
   - **Summary** of the project
   - **Technologies** detected
   - **Code quality** assessment
   - **Issues / bad practices** found
   - **Estimated developer level** (Junior / Mid / Senior)
   - **Improvement suggestions**

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health check — returns `{"status": "ok"}` |

---

## Analysis Report Schema

The Gemini model returns a structured JSON response mapped to the following schema:

```json
{
  "summary": "Project summary...",
  "technologies": ["Python", "FastAPI", "..."],
  "code_quality": "Code structure quality analysis...",
  "issues": ["Issue 1", "Issue 2"],
  "developer_level": "Junior | Mid | Senior",
  "suggestions": ["Suggestion 1", "Suggestion 2"]
}
```
