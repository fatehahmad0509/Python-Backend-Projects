# Transly - Backend

Transly lets users snap a photo or pick an image from their gallery
and get every piece of text inside it detected and translated, powered by
Google Gemini Vision. This repository contains the backend API only.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running with Docker](#running-with-docker)
- [Database Setup](#database-setup)
- [Database Index Strategy](#database-index-strategy)
- [Authentication Flow](#authentication-flow)
- [Redis Caching](#redis-caching)
- [API Reference](#api-reference)
- [Plans & Quotas](#plans--quotas)

## Features

- Register / login with email + password, JWT access + refresh tokens.
- Upload an image, get all text in it detected and translated via Gemini Vision.
- Upload a short video (max 60s), get spoken dialogue and on-screen text detected and translated via Gemini.
- Per-plan daily translation quotas (FREE / PLUS / DEVELOPER), enforced server-side, tracked separately for image and video.
- Paginated translation history, cached in Redis.
- Blocked-user enforcement on every authenticated request.
- Redis-backed rate limiting.

## Architecture

The codebase follows a strict layered architecture:

```
Router  ->  Service  ->  Repository  ->  Database
```

- **Routers** only parse the HTTP request, call a service, and return a
  standard response. They contain no business logic.
- **Services** hold all business logic (quota checks, token issuance, Gemini
  orchestration, cache invalidation, etc.) and depend on repositories and
  other services, never on the database directly.
- **Repositories** are the only layer that issues SQLAlchemy queries.
- Dependencies are wired through FastAPI's `Depends()`, so every layer is
  constructed with its dependencies injected rather than importing globals.

This keeps the code testable (each layer can be mocked in isolation),
readable, and easy to extend without touching unrelated files.

## Folder Structure

```
app/
  main.py                   FastAPI app factory, middleware, routers, lifespan

  core/
    config.py               Environment-driven settings
    security.py             Password hashing (bcrypt)
    logging.py               Logging configuration

  database/
    session.py               Async engine + session factory
    base.py                   Declarative base, registers all models
    redis.py                  Redis connection pool / client factory

  models/
    user.py                  User + PlanEnum
    translation.py           Translation
    daily_usage.py            DailyUsage

  schemas/
    auth.py                   Register/login/refresh/token schemas
    user.py                    UserResponse
    translation.py             Gemini result + history schemas
    common.py                  StandardResponse, PaginationMeta

  routers/
    auth.py                    /auth/*
    users.py                   /users/*
    translations.py            /translate/image, /translations/history

  repositories/
    user_repository.py
    translation_repository.py
    usage_repository.py

  services/
    auth_service.py            Registration, login, refresh rotation
    translation_service.py     Orchestrates the whole translate-image flow
    gemini_service.py          The ONLY place that calls the Gemini API
    usage_service.py           Quota enforcement + retention cleanup
    cache_service.py           All Redis reads/writes

  dependencies/
    auth.py                    get_current_user / get_current_active_user
    database.py                get_db / get_redis

  middlewares/
    blocked_user.py             Fast-path blocked-user rejection
    rate_limit.py                Redis-backed rate limiter

  utils/
    image_validator.py           Pillow-based image validation
    jwt.py                        JWT encode/decode

  constants/
    plans.py                     Plan daily limits, retention window
    errors.py                    Machine-readable error codes

  exceptions/
    custom_exceptions.py         AppException hierarchy
    handlers.py                   Global handlers -> standard error shape
```

## Tech Stack

Python 3.13 - FastAPI - Uvicorn - SQLAlchemy (async) - PostgreSQL (asyncpg) -
Redis - JWT (PyJWT) - Pydantic v2 - Pillow - Google Gemini API - Docker.

> **Note on migrations:** Alembic is intentionally **not** used. Only
> SQLAlchemy models are provided; schema migrations are managed manually.
> As a local/first-run convenience, the app will create any tables that do
> not exist yet on startup (`AUTO_CREATE_TABLES=True`) - it never alters
> existing tables, so it is safe to disable once you manage the schema
> yourself.

## Installation

```bash
git clone <this-repo>
cd transly
cp .env.example .env
# edit .env: at minimum set JWT_SECRET and GEMINI_API_KEY
```

### Run locally (without Docker)

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Make sure PostgreSQL and Redis are running and DATABASE_URL / REDIS_URL
# in .env point to them, then:
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`, with interactive docs
at `http://localhost:8000/docs`.

## Environment Variables

| Variable                      | Description                                         | Default              |
|--------------------------------|------------------------------------------------------|-----------------------|
| `DATABASE_URL`                 | Async Postgres connection string (`asyncpg` driver)   | -                     |
| `REDIS_URL`                    | Redis connection string                               | -                     |
| `JWT_SECRET`                   | Secret used to sign JWTs                              | -                     |
| `JWT_ALGORITHM`                | JWT signing algorithm                                 | `HS256`               |
| `ACCESS_TOKEN_EXPIRE_MINUTES`  | Access token lifetime                                 | `30`                  |
| `REFRESH_TOKEN_EXPIRE_DAYS`    | Refresh token lifetime                                | `30`                  |
| `GEMINI_API_KEY`               | Google Gemini API key                                 | -                     |
| `GEMINI_MODEL`                 | Gemini model used for vision requests                 | `gemini-3.1-flash-lite` |
| `MAX_UPLOAD_SIZE_MB`           | Max accepted image size                               | `10`                  |
| `MAX_IMAGE_DIMENSION`          | Max accepted width/height in pixels                   | `6000`                |
| `MAX_VIDEO_UPLOAD_SIZE_MB`     | Max accepted video size (sent inline to Gemini)       | `19`                  |
| `MAX_VIDEO_DURATION_SECONDS`   | Max accepted video duration                           | `60`                  |
| `RATE_LIMIT_PER_MINUTE`        | Requests allowed per identifier per minute            | `60`                  |
| `AUTO_CREATE_TABLES`           | Create missing tables on startup (dev convenience)    | `True`                |

See `.env.example` for the full list, including Docker Compose Postgres
credentials.

## Running with Docker

```bash
docker compose up --build
```

This starts three services:

- `backend` - the FastAPI app on port `8000`
- `postgres` - PostgreSQL 16 on port `5432`
- `redis` - Redis 7 on port `6379`

## Database Setup

No migration tool is included by design. On first boot, with
`AUTO_CREATE_TABLES=True`, the app creates the `users`, `daily_usages`, and
`translations` tables (and their indexes/constraints) automatically via
`Base.metadata.create_all`. From that point forward, any schema change is
the team's responsibility to apply manually (e.g. hand-written SQL).

Plan changes (`FREE` / `PLUS` / `DEVELOPER`) are applied directly in the
database - there is no payment system or self-service upgrade endpoint.

## Database Index Strategy

**users**
- Unique index on `email` - used for login lookups.
- Unique index on `username` - used for registration uniqueness checks.
- Primary key index on `id` - automatic.

**daily_usages**
- Composite unique index on `(user_id, date)` - a user can only have one
  usage row per day, and the row is always looked up by exactly this pair:
  `WHERE user_id = ? AND date = CURRENT_DATE`.

**translations**
- Composite index on `(user_id, created_at)` - supports the history query
  `WHERE user_id = ? ORDER BY created_at DESC`. A standard ascending
  B-tree index is sufficient since PostgreSQL can scan it backwards just
  as efficiently as forwards.
- No indexes on `response_json`, `detected_languages`, or `target_language`
  since none of them are ever filtered or sorted on.

## Authentication Flow

1. `POST /auth/register` - creates a user with a bcrypt-hashed password.
2. `POST /auth/login` - verifies credentials, rejects blocked accounts,
   returns an access token (30 min) and a refresh token (30 days).
3. Every subsequent request sends `Authorization: Bearer <access_token>`.
4. `POST /auth/refresh` - exchanges a valid, non-revoked refresh token for
   a brand-new access/refresh pair. The old refresh token is immediately
   revoked (rotation), so a stolen-and-reused refresh token is detected
   the moment the legitimate owner refreshes again.

Refresh tokens are tracked in Redis by their unique `jti` claim, which is
what makes rotation/revocation possible without an extra database table.

**Blocked users:** `dependencies.auth.get_current_user` re-checks
`is_blocked` against the database on every request and caches a "blocked"
flag in Redis. `middlewares.blocked_user` uses that cached flag to reject
further requests from a blocked account before they even reach routing.

## Redis Caching

**Translation history** (`GET /translations/history`):

1. Check Redis for the requested page.
2. On a hit, return the cached page directly.
3. On a miss, query PostgreSQL, cache the result for 24 hours, then return it.
4. On new translation creation or history deletion, all cached pages for
   that user are invalidated immediately.

**Refresh tokens**, as described above, and **blocked-user flags** are also
stored in Redis.

## API Reference

All responses use a standard envelope:

```json
{ "success": true, "message": "Success", "data": {} }
```

```json
{ "success": false, "message": "Validation failed", "error": { "code": "VALIDATION_ERROR", "details": {} } }
```

| Method | Path                        | Auth required | Description                              |
|--------|-----------------------------|:--------------:|--------------------------------------------|
| POST   | `/auth/register`             | No             | Create a new account                        |
| POST   | `/auth/login`                 | No             | Log in, receive tokens                      |
| POST   | `/auth/refresh`               | No             | Rotate an expired access token              |
| GET    | `/users/me`                   | Yes            | Current user's profile                      |
| POST   | `/translate/image`            | Yes            | Translate text found in an uploaded image   |
| POST   | `/translate/video`            | Yes            | Translate speech + on-screen text found in an uploaded video (max 60s) |
| GET    | `/translations/history`       | Yes            | Paginated translation history               |
| DELETE | `/translations/history`       | Yes            | Delete all translation history              |
| GET    | `/health`                     | No             | Health check                                |

Full interactive documentation (request/response schemas, try-it-out) is
available at `/docs` once the app is running.

## Plans & Quotas

| Plan      | Daily image translations | Daily video translations |
|-----------|---------------------------|----------------------------|
| FREE      | 5                          | 2                           |
| PLUS      | 25                         | 5                            |
| DEVELOPER | Unlimited                  | Unlimited                    |

Usage is tracked per calendar day in `daily_usages` (`usage_count` for
images, `video_usage_count` for videos - two independent counters,
independently rate-limited), created lazily on first use each day (no
reset job needed). Usage rows older than 10 days are purged automatically
whenever a new usage record is created or updated - there is no separate
cleanup job.

Videos are capped at `MAX_VIDEO_DURATION_SECONDS` (60s) and
`MAX_VIDEO_UPLOAD_SIZE_MB` (19MB) and are sent to Gemini as inline bytes
in a single request (no Files API, no server-side storage of the raw
video - only the translation result is persisted). `ffprobe` (from the
`ffmpeg` package, installed in the Docker image) validates the container
format and duration before any Gemini call is made.

### Migrating an existing database

If you're deploying this on top of a database that already has
`translations` / `daily_usages` tables from before video support was
added, run `migrations/2026_07_add_video_translation_support.sql` by hand
once (see the note at the top of that file - there is no Alembic here,
schema changes are applied manually). Fresh databases don't need it:
`AUTO_CREATE_TABLES` will create both tables with the new columns already
in place.
