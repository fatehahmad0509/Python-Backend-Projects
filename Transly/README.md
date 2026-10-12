# Transly

Transly lets you snap a photo — or a short video — and instantly get every
piece of text and speech in it detected and translated, powered by Google
Gemini. Point it at a menu, a street sign, a screenshot, or a clip with
dialogue and on-screen text, and get a clean, translated breakdown back.

This repository is a monorepo containing both halves of the app:

```
transly/
├── backend/    FastAPI + PostgreSQL + Redis API (Python)
└── frontend/   Next.js web client (TypeScript)
```

## Features

- **Photo translation** — upload or snap a photo; every piece of readable
  text in it is detected, its source language identified, and translated
  into your chosen target language.
- **Video translation** — upload a short video (up to 60 seconds); both the
  spoken dialogue and any on-screen text (captions, signs, UI text) are
  transcribed, language-identified, and translated — in a single Gemini
  call, no separate speech-to-text or OCR pipeline required.
- **Accounts & quotas** — email/password auth with JWT access + refresh
  tokens, and per-plan daily translation limits (FREE / PLUS / DEVELOPER),
  tracked independently for photos and videos.
- **Translation history** — paginated, cached, with a one-click "delete
  all" option.
- **Production-minded backend** — layered architecture (router → service →
  repository → database), Redis-backed caching and rate limiting, blocked-
  user enforcement, and a Dockerized deployment.

## How video translation works

Rather than building a custom pipeline (speech-to-text model + OCR model +
translation model, glued together), Transly sends the raw video straight to
Gemini, which natively understands both the audio track and the visual
frames in a single request. One prompt asks the model to:

1. Transcribe every spoken sentence in the audio track.
2. Detect every piece of readable on-screen text.
3. Identify the source language of each segment individually.
4. Translate everything into the target language.

The video is validated first with `ffprobe` (format, duration, and file
size) before ever reaching Gemini, and is sent as inline bytes — which is
why there's a video size cap (see [Plans & Quotas](#plans--quotas)).

## Tech Stack

**Backend:** Python 3.13 · FastAPI · Uvicorn · SQLAlchemy (async) ·
PostgreSQL (asyncpg) · Redis · PyJWT · Pydantic v2 · Pillow · `ffmpeg`/
`ffprobe` · Google Gemini API · Docker

**Frontend:** Next.js 14 (App Router) · TypeScript · Tailwind CSS

## Getting Started

### 1. Backend

```bash
cd backend
cp .env.example .env
# edit .env: at minimum set JWT_SECRET and GEMINI_API_KEY
```

Run with Docker (starts the API, PostgreSQL, and Redis together):

```bash
docker compose up --build
```

Or run locally without Docker:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# make sure PostgreSQL and Redis are running and DATABASE_URL / REDIS_URL
# in .env point to them, then:
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`.

See [`backend/README.md`](backend/README.md) for the full environment
variable reference, database index strategy, auth flow, and caching
details.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
```

Point `.env.local` at your backend:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Then:

```bash
npm run dev
```

Open `http://localhost:3000`.

See [`frontend/README.md`](frontend/README.md) for how the frontend is
wired to the backend and a page-by-page breakdown.

## API Reference

All responses use a standard envelope:

```json
{ "success": true, "message": "Success", "data": {} }
```

```json
{ "success": false, "message": "Validation failed", "error": { "code": "VALIDATION_ERROR", "details": {} } }
```

| Method | Path                     | Auth required | Description                                                            |
|--------|--------------------------|:--------------:|--------------------------------------------------------------------------|
| POST   | `/auth/register`         | No             | Create a new account                                                    |
| POST   | `/auth/login`            | No             | Log in, receive tokens                                                  |
| POST   | `/auth/refresh`          | No             | Rotate an expired access token                                          |
| GET    | `/users/me`              | Yes            | Current user's profile + quota snapshot                                 |
| POST   | `/translate/image`       | Yes            | Translate text found in an uploaded image                               |
| POST   | `/translate/video`       | Yes            | Translate speech + on-screen text found in an uploaded video (max 60s)  |
| GET    | `/translations/history`  | Yes            | Paginated translation history                                           |
| DELETE | `/translations/history`  | Yes            | Delete all translation history                                          |
| GET    | `/health`                | No             | Health check                                                            |

Full interactive documentation (request/response schemas, try-it-out) is
available at `/docs` once the backend is running.

## Plans & Quotas

| Plan      | Daily photo translations | Daily video translations |
|-----------|--------------------------|----------------------------|
| FREE      | 5                        | 2                          |
| PLUS      | 25                       | 5                          |
| DEVELOPER | Unlimited                | Unlimited                 |

Usage resets daily and is tracked independently for photos and videos.
Plan changes are applied directly in the database — there's no payment
system or self-service upgrade flow.

## Known Limitations

- **Video size cap (19MB) / duration cap (60s).** Videos are sent to
  Gemini as inline request bytes rather than through the separate Files
  API, and Gemini's inline request size is capped around 20MB total
  (video + prompt). Nineteen megabytes is a deliberate, conservative
  margin under that ceiling — not an arbitrary restriction. Supporting
  larger videos reliably would mean switching to Gemini's Files API
  (upload the video separately, then reference it in the generation
  call), which is a reasonable next step but out of scope for now.
- **No automated tests or CI pipeline** — the project has been tested
  manually end-to-end, but doesn't yet include a test suite.
- **No Alembic / migration tool** — schema changes are applied by hand
  (see `backend/migrations/`) rather than through a migration framework.

## License

MIT — see [LICENSE](LICENSE).
