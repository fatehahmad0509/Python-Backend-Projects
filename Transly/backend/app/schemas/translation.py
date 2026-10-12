"""
Translation schemas, including the exact contract used for Gemini responses.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.translation import MediaTypeEnum
from app.schemas.common import PaginationMeta


class TranslationItem(BaseModel):
    source_language: str
    original: str
    translated: str


class GeminiErrorDetail(BaseModel):
    code: str
    message: str


class TranslationResult(BaseModel):
    """
    Shape returned by the Gemini vision service and stored verbatim as
    `response_json` on the Translation model.
    """

    success: bool
    detected_languages: list[str] = Field(default_factory=list)
    target_language: str
    translations: list[TranslationItem] = Field(default_factory=list)
    error: GeminiErrorDetail | None = None


class VideoTranslationItem(BaseModel):
    """
    Same shape as TranslationItem, plus `type` so the client can tell
    spoken dialogue apart from on-screen text (both are detected in the
    same Gemini call).
    """

    type: Literal["speech", "on_screen_text"]
    source_language: str
    original: str
    translated: str


class VideoTranslationResult(BaseModel):
    """
    Shape returned by the Gemini video service and stored verbatim as
    `response_json` on the Translation model (media_type=VIDEO).
    """

    success: bool
    detected_languages: list[str] = Field(default_factory=list)
    target_language: str
    translations: list[VideoTranslationItem] = Field(default_factory=list)
    error: GeminiErrorDetail | None = None


class TranslationHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    media_type: MediaTypeEnum
    detected_languages: list[str]
    target_language: str
    response_json: dict
    created_at: datetime


class PaginatedTranslationHistory(BaseModel):
    items: list[TranslationHistoryItem]
    pagination: PaginationMeta
