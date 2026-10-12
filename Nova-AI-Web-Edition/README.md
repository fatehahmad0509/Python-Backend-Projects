# Nova AI 🚀

Nova AI is a comprehensive AI-powered assistant platform featuring chat capabilities, web search integration, and user-specific usage tracking. It leverages modern LLM technology to provide intelligent, real-time responses with a seamless user interface.

## ✨ Features

- **Conversational AI:** Powered by Google Gemini with customizable system prompts.
- **Web Search Integration:** Real-time information retrieval via Tavily search grounding.
- **Image Support:** Ability to process and analyze images within chat interactions.
- **Token Usage Tracking:** Detailed daily monitoring of prompt and completion token usage.
- **User Plans:** Tier-based access control (Free, Plus, Pro, Developer).
- **Secure Authentication:** JWT-based authentication system.
- **Robust Backend:** Built with FastAPI, featuring async database operations and migrations via Alembic.
- **Responsive UI:** Modern React-based frontend styled with Tailwind CSS.

## 🛠️ Technology Stack

### Backend
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **Database:** PostgreSQL (managed via SQLAlchemy & Alembic)
- **Caching/Queue:** Redis
- **LLM Engine:** Google Generative AI (Gemini)
- **Search Tool:** Tavily API
- **Auth:** PyJWT & bcrypt

### Frontend
- **Framework:** React + TypeScript
- **Styling:** Tailwind CSS
- **Build Tool:** Vite

## 🚀 Setup & Installation

### Prerequisites
- Docker & Docker Compose
- Python 3.13+
- Node.js 18+

### Backend Setup
1. Navigate to `Nova-AI-Backend/`.
2. Create a `.env` file based on `env.example`.
3. Configure your `DATABASE_URL` (Neon PostgreSQL recommended), `GEMINI_API_KEY`, and `TAVILY_API_KEY`.
4. Run the services using Docker:
   ```bash
   docker-compose up --build
   ```

### Frontend Setup
1. Navigate to `Nova-AI-Frontend/`.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

## ⚙️ Configuration (.env)

The following environment variables are required for the application to function:

| Variable | Description |
| :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis instance URL |
| `JWT_SECRET` | Secret key for signing tokens |
| `GEMINI_API_KEY` | Google Gemini API key |
| `TAVILY_API_KEY` | Tavily API key for web search |
| `FRONTEND_ORIGIN` | Allowed CORS origin (default: localhost:3000) |

## 📁 Project Structure

```text
Nova-AI/
├── Nova-AI-Backend/      # FastAPI application, DB migrations, Services
│   ├── app/              # Core logic, API endpoints, Models, Services
│   └── alembic/          # Database migrations
└── Nova-AI-Frontend/     # React + TypeScript SPA
    ├── src/              # Components, Hooks, API, State management
    └── public/           # Static assets
```

## 🧪 Testing

The backend includes a comprehensive suite of tests covering:
- Authentication & Authorization
- Chat functionality and search integration
- Token usage tracking and retention policies
- User account management

Run tests using `pytest` within the backend environment:
```bash
pytest tests/
```

## 📄 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.