"""Validation and decoding helpers for user-supplied images (vision input).

Images arrive from clients as base64 strings (optionally as a data URL,
e.g. "data:image/png;base64,...."). This module turns that into raw bytes
Gemini can consume, while rejecting anything malformed, oversized, or of
an unsupported type before it ever reaches the model.
"""
import base64
import binascii

from app.config import settings
from app.core.exceptions import InvalidImageError

# Mime types Gemini's vision models accept.
SUPPORTED_IMAGE_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/heic",
    "image/heif",
}


def decode_base64_image(image_base64: str, mime_type: str) -> bytes:
    """Validate and decode a base64-encoded image.

    Raises InvalidImageError if the mime type is unsupported, the base64
    payload is malformed, or the decoded image exceeds the configured
    size limit.
    """
    if mime_type not in SUPPORTED_IMAGE_MIME_TYPES:
        raise InvalidImageError(
            f"Unsupported image type '{mime_type}'. Supported types: "
            f"{', '.join(sorted(SUPPORTED_IMAGE_MIME_TYPES))}."
        )

    raw = image_base64
    if raw.startswith("data:"):
        # Strip a data URL prefix like "data:image/png;base64," if present.
        _, _, raw = raw.partition(",")

    if not raw:
        raise InvalidImageError("The provided image is empty.")

    try:
        image_bytes = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise InvalidImageError("The provided image is not valid base64.") from exc

    if not image_bytes:
        raise InvalidImageError("The provided image is empty.")

    max_bytes = int(settings.max_image_size_mb * 1024 * 1024)
    if len(image_bytes) > max_bytes:
        raise InvalidImageError(
            f"The image exceeds the maximum allowed size of {settings.max_image_size_mb}MB."
        )

    return image_bytes
