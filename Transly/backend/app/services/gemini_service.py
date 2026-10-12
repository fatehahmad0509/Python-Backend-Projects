"""
Gemini Vision service.

This is the ONLY place in the application that talks to the Google Gemini
API. Routers must never call Gemini directly - they always go through
`TranslationService`, which in turn depends on this service.
"""

import json
import logging

from google import genai
from google.genai import types

from app.core.config import settings
from app.exceptions.custom_exceptions import GeminiServiceException
from app.schemas.translation import TranslationResult, VideoTranslationResult

logger = logging.getLogger("transly.gemini")

_PROMPT_TEMPLATE = """You are an OCR and translation engine embedded in a mobile app.

Analyze the attached image and:
1. Detect every piece of readable text in the image.
2. Identify the language of each detected text segment.
3. Translate every detected text segment into the target language: {target_language}.

Respond with STRICT JSON only, and nothing else (no Markdown, no backticks,
no explanation), matching exactly this schema:

{{
  "success": true,
  "detected_languages": ["English", "Japanese"],
  "target_language": "{target_language}",
  "translations": [
    {{"source_language": "English", "original": "Exit", "translated": "translated text here"}}
  ],
  "error": null
}}

If no readable text can be found anywhere in the image, respond with exactly:

{{
  "success": false,
  "detected_languages": [],
  "target_language": "{target_language}",
  "translations": [],
  "error": {{"code": "TEXT_NOT_READABLE", "message": "The text in the image could not be recognized."}}
}}
"""

_VIDEO_PROMPT_TEMPLATE = """You are a speech transcription, OCR and translation engine embedded in \
a mobile app.

Analyze the attached video (both its audio track and its visual frames) and:
1. Transcribe every distinct spoken sentence or phrase in the audio track, in the order it occurs.
2. Detect every piece of readable on-screen text that appears in the video (titles, captions, \
signs, subtitles baked into the footage, UI text, etc.), in the order it first appears.
3. Identify the source language of each detected speech segment and each detected on-screen text \
segment individually - a single video may mix languages.
4. Translate every detected segment into the target language: {target_language}.
5. Set "type" to "speech" for anything transcribed from the audio track, or "on_screen_text" for \
anything read visually from a frame.

Keep segments short and natural (one sentence or on-screen phrase per item) rather than merging \
the whole transcript into one giant block.

Respond with STRICT JSON only, and nothing else (no Markdown, no backticks,
no explanation), matching exactly this schema:

{{
  "success": true,
  "detected_languages": ["English", "Japanese"],
  "target_language": "{target_language}",
  "translations": [
    {{"type": "speech", "source_language": "English", "original": "Welcome back!", \
"translated": "translated text here"}},
    {{"type": "on_screen_text", "source_language": "Japanese", "original": "\u55b6\u696d\u4e2d", \
"translated": "translated text here"}}
  ],
  "error": null
}}

If there is no audible speech AND no readable on-screen text anywhere in the video, respond with \
exactly:

{{
  "success": false,
  "detected_languages": [],
  "target_language": "{target_language}",
  "translations": [],
  "error": {{"code": "NOTHING_DETECTED_IN_VIDEO", "message": "No speech or readable text could be \
found in the video."}}
}}
"""


class GeminiService:
    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def translate_image(
        self, image_bytes: bytes, mime_type: str, target_language: str
    ) -> TranslationResult:
        prompt = _PROMPT_TEMPLATE.format(target_language=target_language)

        try:
            response = await self._client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
        except Exception as exc:  # noqa: BLE001 - any SDK/network failure is a service failure
            logger.exception("Gemini API call failed")
            raise GeminiServiceException(
                "Failed to communicate with the translation service"
            ) from exc

        raw_text = (getattr(response, "text", None) or "").strip()
        if not raw_text:
            logger.error("Gemini returned an empty response")
            raise GeminiServiceException("Received an empty response from the translation service")

        try:
            parsed = json.loads(raw_text)
            return TranslationResult.model_validate(parsed)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Failed to parse Gemini response as JSON: %s", raw_text)
            raise GeminiServiceException(
                "Received an invalid response from the translation service"
            ) from exc

    async def translate_video(
        self, video_bytes: bytes, mime_type: str, target_language: str
    ) -> VideoTranslationResult:
        prompt = _VIDEO_PROMPT_TEMPLATE.format(target_language=target_language)

        try:
            response = await self._client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[
                    types.Part.from_bytes(data=video_bytes, mime_type=mime_type),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
        except Exception as exc:  # noqa: BLE001 - any SDK/network failure is a service failure
            logger.exception("Gemini API call failed (video)")
            raise GeminiServiceException(
                "Failed to communicate with the translation service"
            ) from exc

        raw_text = (getattr(response, "text", None) or "").strip()
        if not raw_text:
            logger.error("Gemini returned an empty response (video)")
            raise GeminiServiceException("Received an empty response from the translation service")

        try:
            parsed = json.loads(raw_text)
            return VideoTranslationResult.model_validate(parsed)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Failed to parse Gemini video response as JSON: %s", raw_text)
            raise GeminiServiceException(
                "Received an invalid response from the translation service"
            ) from exc
