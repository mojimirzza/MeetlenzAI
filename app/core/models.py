from __future__ import annotations
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Lifecycle(StrEnum):
    INTAKE = "INTAKE"
    NORMALIZED = "NORMALIZED"
    REPRESENTED = "REPRESENTED"
    CLUSTERED = "CLUSTERED"
    NOMINATED = "NOMINATED"
    PRIORITIZED = "PRIORITIZED"
    MODERATION_PENDING = "MODERATION_PENDING"
    APPROVED = "APPROVED"
    EDITED = "EDITED"
    REJECTED = "REJECTED"
    ASKED = "ASKED"
    ANSWERED = "ANSWERED"
    DEFERRED = "DEFERRED"
    CLOSED = "CLOSED"


class ModeratorAction(StrEnum):
    APPROVE = "approve"
    EDIT = "edit"
    REJECT = "reject"


class MeetingCreate(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    domain: str = Field(default="general", max_length=120)
    agenda: str = Field(default="", max_length=4000)
    manager_user_id: str = Field(default="moderator", max_length=100)


class ParticipantCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    display_name: str = Field(min_length=1, max_length=200)
    expertise: list[str] = Field(default_factory=list)


class QuestionCreate(BaseModel):
    meeting_id: str
    user_id: str
    text: str = Field(min_length=3, max_length=2000)
    expertise: list[str] = Field(default_factory=list)


class LikeCreate(BaseModel):
    question_id: str
    user_id: str


class ModerationDecision(BaseModel):
    category_id: str
    action: ModeratorAction
    nominee_id: str | None = None
    edited_text: str | None = Field(default=None, max_length=2000)
    moderator_user_id: str
    reason: str = Field(default="", max_length=2000)


class OutcomeCreate(BaseModel):
    asked_question_id: str
    outcome: str = Field(pattern="^(answered|partially_answered|unanswered|deferred)$")
    usefulness: int | None = Field(default=None, ge=1, le=5)
    notes: str = Field(default="", max_length=2000)


class MeetingSnapshot(BaseModel):
    meeting_id: str
    title: str
    domain: str
    agenda: str
    manager_user_id: str
    participant_count: int
    question_count: int
    category_count: int


class Nominee(BaseModel):
    nominee_id: str
    text: str
    source_question_ids: list[str]
    semantic_distinctiveness: float = 0.0
    quality_score: float = 0.0
    evaluation: dict[str, float] = Field(default_factory=dict)
    rationale: str = ""


class QuestionCategory(BaseModel):
    category_id: str
    label: str
    intent: str
    source_question_ids: list[str]
    nominees: list[Nominee]
    priority_score: float = 0.0
    priority_explanation: dict[str, float] = Field(default_factory=dict)


class PipelineResult(BaseModel):
    categories: list[QuestionCategory]
    prompt_version: str
    model_name: str
    fallback: bool = False
    meta: dict[str, Any] = Field(default_factory=dict)
