# QuizBot - AI-Powered Telegram Quiz Generator

QuizBot is an advanced Telegram bot that dynamically generates multiple-choice quiz questions on any user-specified topic and quantity using AI (Anthropic Claude API). It manages generation limits on a per-user basis and delivers the final quiz as a sleek, professional PDF report.

This project represents a complete backend implementation, showcasing asynchronous programming, LLM integration, relational database management, and dynamic document generation.

## 🚀 Key Features

* **AI-Powered Question Generation:** Integrates with the Anthropic Claude API to generate entirely unique, contextually accurate, and properly formatted multiple-choice questions.
* **Smart Batch Management:** Breaks down high-volume question requests into smaller batches, processing them asynchronously to bypass API rate limits and prevent timeouts.
* **Dynamic PDF Reporting:** Compiles the generated questions into an organized, corporate, and highly readable PDF file using the `ReportLab` library, delivering it instantly via Telegram.
* **Advanced Whitelist & Limit Control:** Powered by a PostgreSQL database to track and enforce users' daily and total question generation limits in real-time, ensuring system security.
* **Asynchronous Architecture:** Built on top of the `python-telegram-bot` library's `async/await` pattern to achieve high concurrency and optimal performance.

---

## 🛠 Tech Stack & Libraries

* **Language:** Python 3.10+
* **Bot Framework:** `python-telegram-bot` (Async)
* **LLM API:** `Anthropic Claude API` (via `asyncio` executors)
* **Database:** `PostgreSQL` (Connection pooling and management via `psycopg2`)
* **Reporting:** `ReportLab` (Dynamic PDF generation and custom font management)
* **Environment Management:** `python-dotenv`

---

## 📁 Project Structure

```text
├── main.py          # Main bot loop, command handlers, and Telegram integration
├── db.py            # PostgreSQL database connections, whitelist, and limit queries
├── pdf.py           # Module that transforms quiz data into dynamic PDF reports
├── requirements.txt # Project dependencies list
└── .env.example     # Environment variables template (Contains no sensitive data)

```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/QuizBot.git
cd QuizBot

```

### 2. Install Dependencies

```bash
pip install -r requirements.txt

```

### 3. Configure Environment Variables

Create a `.env` file in the root directory based on the `.env.example` template and fill in your credentials:

```ini
BOT_TOKEN=your_telegram_bot_token_here
ANTHROPIC_API_KEY=your_claude_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

```

### 4. Run the Bot

```bash
python main.py

```

---

## 🔒 Security & Production Notes

* **Cloud Ready:** The project is fully compatible with the `DATABASE_URL` and environment variable architecture, making it ready for seamless deployment on cloud platforms like Render, Heroku, or AWS.
* **Data Safety:** To prevent sensitive data (API keys, DB credentials) from leaking into GitHub, the `.gitignore` configuration is strictly implemented, ensuring the `.env` file is never pushed to the repository.