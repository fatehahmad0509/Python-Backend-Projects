"""
Image validation utility.

Validates uploaded images before they are ever sent to Gemini:
- Rejects empty uploads.
- Enforces a maximum file size.
- Uses Pillow to actually decode the image (rejecting fake extensions -
  a `.png` that is really a text file, an executable, etc. will fail here).
- Restricts accepted formats to JPEG, PNG and WEBP.
- Rejects extremely large resolutions to protect against decompression
  bomb style attacks and to keep Gemini request payloads reasonable.
"""

import io

from PIL import Image, UnidentifiedImageError

from app.core.config import settings
from app.exceptions.custom_exceptions import InvalidImageException

SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}


def validate_image(file_bytes: bytes) -> Image.Image:
    """Validate raw image bytes and return the decoded Pillow image."""
    max_file_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    if not file_bytes:
        raise InvalidImageException("Uploaded image is empty")

    if len(file_bytes) > max_file_size_bytes:
        raise InvalidImageException(
            f"Image exceeds the maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB"
        )

    try:
        probe = Image.open(io.BytesIO(file_bytes))
        probe.verify()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidImageException("Uploaded file is not a valid image") from exc

    try:
        # verify() leaves the file object in a state that cannot be used for
        # further operations, so the image is reopened for actual use.
        image = Image.open(io.BytesIO(file_bytes))
        image.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidImageException("Uploaded file is not a valid image") from exc

    if image.format not in SUPPORTED_FORMATS:
        raise InvalidImageException(
            f"Unsupported image format '{image.format}'. "
            "Supported formats are: JPG, JPEG, PNG, WEBP"
        )

    width, height = image.size
    if width > settings.MAX_IMAGE_DIMENSION or height > settings.MAX_IMAGE_DIMENSION:
        raise InvalidImageException(
            "Image resolution exceeds the maximum allowed dimension of "
            f"{settings.MAX_IMAGE_DIMENSION}px"
        )

    return image
