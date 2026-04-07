from __future__ import annotations

from pydantic import BaseModel, Field


class DraftEmail(BaseModel):
    subject: str
    body: str


class GeneratedEmail(BaseModel):
    subject: str = Field(min_length=5, max_length=150)
    body: str = Field(min_length=100, max_length=1500)


class GenerationMetadata(BaseModel):
    word_count: int
    warnings: list[str] = []
