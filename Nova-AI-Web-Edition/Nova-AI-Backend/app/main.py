"""Nova AI backend application entrypoint."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, chat, users
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.db.session import engine
from app.services.token_usage_retention_service import run_token_usage_retention_loop
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


def _harden_set_cookie(value: str) -> str:
    """Add missing Secure / HttpOnly / SameSite flags to a Set-Cookie header value.
    Does nothing if the flag already exists.

    This prevents cookies from leaking out with missing flags even if the
    application itself does not set cookies (it currently does not), but an
    intermediate proxy/infrastructure layer or a dependency added later does.
    """
    parts = [p.strip() for p in value.split(";") if p.strip()]
    if not parts:
        return value

    attr_names = {p.split("=", 1)[0].strip().lower() for p in parts[1:]}

    if "secure" not in attr_names:
        parts.append("Secure")
    if "httponly" not in attr_names:
        parts.append("HttpOnly")
    if "samesite" not in attr_names:
        parts.append("SameSite=Lax")

    return "; ".join(parts)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # If a Set-Cookie header exists (from the app or another layer),
        # forcibly add Secure/HttpOnly/SameSite flags.
        new_raw_headers = []
        for name, value in response.raw_headers:
            if name.lower() == b"set-cookie":
                hardened = _harden_set_cookie(value.decode("latin-1"))
                new_raw_headers.append((name, hardened.encode("latin-1")))
            else:
                new_raw_headers.append((name, value))
        response.raw_headers = new_raw_headers

        # HSTS - force HTTPS (1 year, include subdomains, preload)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # CSP - You can test in Report-Only mode first
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "  # needed if inline CSS exists
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "  # Clickjacking protection
            "base-uri 'self'; "
            "form-action 'self';"
        )

        # Clickjacking protection (double protection with CSP frame-ancestors)
        response.headers["X-Frame-Options"] = "DENY"

        # MIME sniffing protection
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Restrict browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=(), "
            "gyroscope=(), fullscreen=(self)"
        )

        # Extra: limit referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Nova AI backend starting up (environment=%s)", settings.environment)
    retention_task = asyncio.create_task(run_token_usage_retention_loop())
    yield
    logger.info("Nova AI backend shutting down")
    retention_task.cancel()
    try:
        await retention_task
    except asyncio.CancelledError:
        pass
    await engine.dispose()


_is_production = settings.environment.lower() == "production"

app = FastAPI(
    title="Nova AI",
    description="Production backend for the Nova AI chat assistant.",
    version="1.0.0",
    lifespan=lifespan,
    servers=[{"url": settings.backend_url, "description": settings.environment}],
    # Swagger UI / ReDoc / OpenAPI schema is disabled in production;
    # only accessible in development and other environments.
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(chat.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Basic liveness endpoint."""
    return {"success": True, "message": "Nova AI backend is running", "error": None}
