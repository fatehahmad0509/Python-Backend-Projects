# Studify 🚀

Studify is an intelligent, AI-powered study companion designed to enhance learning through gamification, automated content summarization, and interactive study tools.

---

## ✨ Features

*   **AI-Powered Learning:** Leverages Google's Gemini models for text analysis, image OCR, and study assistance.
*   **Gamification:** Track your progress with XP points, levels, and daily streaks to stay motivated.
*   **Smart Quotas:** Dynamic usage limits based on subscription plans (FREE/PLUS).
*   **Interactive Tools:** Create flashcards, generate quizzes, and get automated summaries of your study materials.
*   **Secure Authentication:** JWT-based secure user authentication.
*   **High Performance:** Built with FastAPI and asynchronous database operations for low-latency responses.

---

## 🛠 Tech Stack

*   **Backend:** FastAPI (Python)
*   **Database:** PostgreSQL (via SQLAlchemy & `asyncpg`)
*   **AI Engine:** Google Gemini API
*   **Authentication:** JWT, Passlib (bcrypt)
*   **Frontend:** HTML5, Service Workers (PWA support)

---

## 📂 Project Structure

```text
Studify/
├── backend/          # FastAPI application
│   ├── routes/       # API endpoints (auth, quiz, flashcards, etc.)
│   ├── models.py     # SQLAlchemy database models
│   ├── gemini_service.py # Gemini AI integration
│   └── main.py       # Application entry point
├── frontend/         # Static assets and PWA configuration
└── .env              # Environment variables (not tracked)
```

---

## ⚙️ Configuration

Create a `.env` file in the root directory with the following variables:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/studify
SECRET_KEY=your_super_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
GEMINI_API_KEY=your_gemini_api_key
```

---

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/studify.git
   cd Studify
   ```

2. **Setup Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Run the Application:**
   ```bash
   uvicorn main:app --reload
   ```

---

## 📚 Key Dependencies (backend/requirements.txt)

*   `fastapi`: Web framework
*   `sqlalchemy`: ORM for database interaction
*   `asyncpg`: PostgreSQL driver for async operations
*   `google-genai`: Integration for Gemini AI models
*   `python-jose`: JWT token handling
*   `passlib`: Password hashing

---

## ⚖️ License

This project is proprietary. All rights reserved.