# Nova-AI-Backend

Nova-AI-Backend is a robust, high-performance API service built with FastAPI, designed to power advanced AI-driven conversational interfaces. It integrates Google's Gemini AI and Tavily for web-search-grounded responses, complete with user authentication, conversation management, and token usage tracking.

---

## 🚀 Features

*   **Authentication & Security**: Secure JWT-based authentication with registration, login, and token refresh workflows.
*   **AI Conversational Engine**: Integration with Google Gemini for intelligent text generation.
*   **Web Search Grounding**: Real-time web search capabilities powered by Tavily to provide up-to-date information.
*   **Usage Tracking**: Granular tracking of prompt/completion tokens and search request counts per user/plan.
*   **Conversation Management**: Persistent storage for chat history, including support for image inputs.
*   **Rate Limiting**: Built-in protection for critical endpoints using Redis.
*   **Database Migrations**: Automated schema versioning via Alembic.
*   **Infrastructure Ready**: Containerized with Docker and support for PostgreSQL (managed via external services like Neon).

---

## 🛠 Tech Stack

*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
*   **Language**: Python 3.13
*   **Database**: PostgreSQL (via SQLAlchemy 2.0 & AsyncPG)
*   **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
*   **Caching/Rate Limiting**: [Redis](https://redis.io/)
*   **AI Integration**: [Google Generative AI](https://ai.google.dev/), [Tavily AI](https://tavily.com/)
*   **Containerization**: Docker & Docker Compose

---

## ⚙️ Configuration

Copy the `env.example` file to `.env` and configure the following variables:

| Variable | Description |
| :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection URL |
| `JWT_SECRET` | Secret key for JWT signing |
| `GEMINI_API_KEY` | Google Gemini API credentials |
| `TAVILY_API_KEY` | Tavily API key for web search |
| `FRONTEND_ORIGIN` | Allowed CORS origin (default: http://localhost:3000) |

---

## 📦 Installation & Running

### Using Docker (Recommended)
Ensure you have Docker and Docker Compose installed.

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd Nova-AI-Backend
   ```
2. Configure your `.env` file based on `env.example`.
3. Start the services:
   ```bash
   docker-compose up --build
   ```
The backend will be available at `http://localhost:8000`.

---

## 📂 Project Structure

```text
Nova-AI-Backend/
├── alembic/            # Database migration scripts
├── app/                # Main application code
│   ├── api/            # API route handlers
│   ├── core/           # Security, auth, logging, & middleware
│   ├── db/             # Database session & models
│   ├── models/         # SQLAlchemy database models
│   ├── repositories/   # Data access layer
│   ├── schemas/        # Pydantic validation models
│   ├── services/       # Business logic (Gemini, Tavily, Auth)
│   └── utils/          # Helpers (image processing, token estimation)
├── tests/              # Pytest suites
├── Dockerfile          # Container definition
└── docker-compose.yml  # Local development orchestration
```

---

## 🧪 Testing

The project uses `pytest` with `pytest-asyncio`. To run tests locally:

```bash
pip install -r requirements.txt
pytest
```

---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.