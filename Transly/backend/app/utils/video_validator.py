"""
Video validation utility.

Validates uploaded videos before they are ever sent to Gemini:
- Rejects empty uploads.
- Enforces a maximum file size (kept well under Gemini's 20MB inline
  request cap, since videos are sent as inline bytes, not via the Files
  API - see core.config for the reasoning).
- Shells out to `ffprobe` (bundled with the `ffmpeg` package installed in
  the Docker image) to actually probe the container: this rejects fake
  extensions the same way Pillow's `Image.open` does for images, and is
  the only reliable way to read video duration without decoding frames.
- Enforces a maximum duration (default 60 seconds).
- Restricts accepted formats to MP4, MOV (QuickTime) and WEBM - the
  formats Gemini documents support and that cover the vast majority of
  phone-recorded and downloaded clips.
"""

import asyncio
import json
import tempfile

from app.core.config import settings
from app.exceptions.custom_exceptions import InvalidVideoException

# Maps ffprobe's `format_name` (comma-separated list of matching container
# formats) to the MIME type Gemini expects. Checked via substring match
# since ffprobe often reports multiple aliases (e.g. "mov,mp4,m4a,3gp,3g2,mj2").
_SUPPORTED_FORMATS: dict[str, str] = {
    "mp4": "video/mp4",
    "mov": "video/quicktime",
    "webm": "video/webm",
}


async def _run_ffprobe(path: str) -> dict:
    proc = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _stderr = await proc.communicate()
    if proc.returncode != 0 or not stdout:
        raise InvalidVideoException("Uploaded file is not a valid video")

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise InvalidVideoException("Uploaded file is not a valid video") from exc


async def validate_video(file_bytes: bytes) -> str:
    """
    Validate raw video bytes and return the Gemini-compatible MIME type.

    Raises InvalidVideoException on any validation failure (empty file,
    oversized file, corrupt/undecodable container, unsupported format, or
    a duration over MAX_VIDEO_DURATION_SECONDS).
    """
    max_file_size_bytes = settings.MAX_VIDEO_UPLOAD_SIZE_MB * 1024 * 1024

    if not file_bytes:
        raise InvalidVideoException("Uploaded video is empty")

    if len(file_bytes) > max_file_size_bytes:
        actual_mb = len(file_bytes) / (1024 * 1024)
        raise InvalidVideoException(
            f"Video is {actual_mb:.1f} MB, which exceeds the maximum allowed size of "
            f"{settings.MAX_VIDEO_UPLOAD_SIZE_MB} MB"
        )

    # ffprobe needs a real file path - there is no reliable way to probe a
    # container format/duration from an in-memory buffer alone.
    with tempfile.NamedTemporaryFile(suffix=".bin") as tmp:
        tmp.write(file_bytes)
        tmp.flush()

        probe = await _run_ffprobe(tmp.name)

        fmt = probe.get("format", {})
        format_name = (fmt.get("format_name") or "").lower()

        mime_type = next(
            (mime for key, mime in _SUPPORTED_FORMATS.items() if key in format_name),
            None,
        )
        if mime_type is None:
            raise InvalidVideoException(
                "Unsupported video format. Supported formats are: MP4, MOV, WEBM"
            )

        has_video_stream = any(
            stream.get("codec_type") == "video" for stream in probe.get("streams", [])
        )
        if not has_video_stream:
            raise InvalidVideoException("Uploaded file does not contain a video stream")

        duration_raw = fmt.get("duration")
        try:
            duration_seconds = float(duration_raw) if duration_raw is not None else None
        except ValueError:
            duration_seconds = None

        if duration_seconds is None:
            raise InvalidVideoException("Could not determine the video's duration")

        if duration_seconds > settings.MAX_VIDEO_DURATION_SECONDS:
            raise InvalidVideoException(
                "Video exceeds the maximum allowed duration of "
                f"{settings.MAX_VIDEO_DURATION_SECONDS} seconds"
            )

    return mime_type
