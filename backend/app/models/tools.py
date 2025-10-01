from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class SessionPayload(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")


class Question(BaseModel):
    id: str
    skill: str
    difficulty: int
    type: str
    prompt: str
    weight: float
    meta: dict[str, Any] = Field(default_factory=dict)


class GetNextQuestionResponse(BaseModel):
    question: Question | None
    rating_summary: dict[str, float] = Field(default_factory=dict)
    plan_index: int | None = None
    remaining: int | None = None
    completed: bool = False


class GradeAnswerPayload(BaseModel):
    session_id: str
    question_id: str
    answer_payload: dict[str, Any]


class GradeAnswerResponse(BaseModel):
    score: float
    objective: Optional[dict[str, Any]] = None
    notes: Optional[str] = None
    auto_feedback: Optional[str] = None
    confidence: Optional[float] = None


class RecordOutcomePayload(BaseModel):
    session_id: str
    question_id: str
    score: float
    time_ms: int
    difficulty: int
    meta: dict[str, Any] = Field(default_factory=dict)


class RecordOutcomeResponse(BaseModel):
    ok: bool
    rating_summary: dict[str, float] = Field(default_factory=dict)


class UpdateDifficultyResponse(BaseModel):
    new_level: int
    rationale: str


class FinalizeSessionResponse(BaseModel):
    report_url: str
    summary: str


class LogInteractionPayload(BaseModel):
    session_id: str
    event_type: Literal[
        "question_asked",
        "answer_received",
        "feedback_shared",
        "hint_requested",
        "timer_mark",
        "plan",
        "reflection",
        "anomaly",
    ]
    payload: dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LogInteractionResponse(BaseModel):
    ok: bool
