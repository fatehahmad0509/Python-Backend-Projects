# Transly — Web

Next.js (App Router + TypeScript + Tailwind) frontend for the Transly backend.
Covers register/login, photo upload + translation, translation history, and
the daily quota badge.

## Setup

```bash
npm install
cp .env.local.example .env.local
```

Edit `.env.local` and point it at your deployed (or local) backend:

```
NEXT_PUBLIC_API_URL=https://your-transly-backend.onrender.com
```

Then:

```bash
npm run dev
```

Open http://localhost:3000.

## How it's wired to the backend

- `src/lib/types.ts` — TypeScript types mirroring the backend's Pydantic
  schemas exactly (`StandardResponse`, `UserProfile`, `TranslationResult`,
  etc.). Keep these in sync if you change the backend's `app/schemas/*`.
- `src/lib/api.ts` — one function per endpoint (`register`, `login`,
  `refreshTokens`, `getMe`, `translateImage`, `translateVideo`, `getHistory`,
  `deleteHistory`). Every function throws `ApiError` (with the backend's
  error `code`) on failure.
- `src/lib/auth-context.tsx` — stores the access/refresh token pair in
  `localStorage`, rehydrates the session on load, and exposes `withAuth()`,
  which transparently refreshes an expired access token and retries the
  request once — pages never have to think about token expiry.
- `src/lib/friendly-error.ts` — maps backend error codes (e.g.
  `DAILY_LIMIT_EXCEEDED`) to plain-language messages shown in the UI.

## Pages

| Route              | Purpose                                              |
| ------------------- | ----------------------------------------------------- |
| `/login`            | Sign in                                                |
| `/register`         | Create an account (auto logs in after, since `/auth/register` doesn't return tokens) |
| `/translate`        | Upload a photo, pick a target language, see results   |
| `/translate/video`  | Upload a short video, see translated speech + on-screen text |
| `/history`          | Paginated translation history, expandable, clear-all  |

`/` just redirects to `/translate` or `/login` depending on session state.

## Target language list

The backend's `target_language` field accepts free text (it's forwarded
straight into the Gemini prompt). Rather than a free-text input, this UI
uses a fixed dropdown (`TARGET_LANGUAGES` in `src/lib/types.ts`) so every
request sends one exact, known-good string. Add more languages there as
needed.

## Notes for production

- Update the backend's `CORS_ORIGINS` env var to your deployed frontend
  domain once you have one (it's currently `["*"]`, which works but is
  broader than necessary).
- Access tokens live 30 minutes; the app refreshes them automatically, but a
  fully expired refresh token logs the user out and redirects to `/login`.
