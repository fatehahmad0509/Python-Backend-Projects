import logging

# Configure basic logging for the application
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger("repolens_bot")
# We can reduce spam from httpx
logging.getLogger("httpx").setLevel(logging.WARNING)
