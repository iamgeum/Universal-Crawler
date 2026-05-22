"""Pydantic 스키마 — Planner 출력, 엔진 출력, Job 상태머신."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

SENSITIVE_KEYS = {
    "api_key",
    "token",
    "password",
    "session",
    "cookie",
    "secret",
    "authorization",
}
SENSITIVE_RE = re.compile(r"(token|key|passwd|auth)=([^&\s\"']+)", re.IGNORECASE)

EngineName = Literal["scrapling", "gallery-dl", "yt-dlp", "patchright"]


def _mask_sensitive(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            k: "***" if k.lower() in SENSITIVE_KEYS else _mask_sensitive(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_mask_sensitive(item) for item in obj]
    if isinstance(obj, str):
        return SENSITIVE_RE.sub(r"\1=***", obj)
    return obj


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_RETRY = "waiting_retry"
    FALLBACK = "fallback_running"
    PARTIAL_SUCCESS = "partial_success"
    MANUAL_REVIEW = "manual_review"
    COMPLETED = "completed"
    FAILED = "failed"


# 허용 상태 전이 (Phase 1c에서 실행 레이어가 사용)
ALLOWED_TRANSITIONS: dict[JobState, set[JobState]] = {
    JobState.QUEUED: {JobState.RUNNING},
    JobState.RUNNING: {
        JobState.COMPLETED,
        JobState.FAILED,
        JobState.PARTIAL_SUCCESS,
    },
    JobState.FAILED: {JobState.WAITING_RETRY, JobState.MANUAL_REVIEW},
    JobState.WAITING_RETRY: {JobState.RUNNING, JobState.FALLBACK},
    JobState.FALLBACK: {JobState.COMPLETED, JobState.FAILED, JobState.MANUAL_REVIEW},
    JobState.PARTIAL_SUCCESS: {JobState.COMPLETED, JobState.FAILED},
    JobState.MANUAL_REVIEW: set(),
    JobState.COMPLETED: set(),
}


class CrawlEvent(BaseModel):
    job_id: int
    event_type: str
    payload: dict = Field(default_factory=dict)

    @field_validator("payload")
    @classmethod
    def mask_sensitive_recursive(cls, v: dict) -> dict:
        return _mask_sensitive(v)


class RetryPolicy(BaseModel):
    max_retries: int = 3
    backoff: Literal["linear", "exponential"] = "exponential"


class CrawlStrategy(BaseModel):
    engine: EngineName
    priority: int = 1
    timeout: int = 30
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    fallback_chain: list[str] = Field(default_factory=lambda: ["patchright"])
    telemetry_tags: list[str] = Field(default_factory=list)
    selectors: dict = Field(default_factory=dict)
    mandatory_fields: list[str] = Field(default_factory=list)
    optional_fields: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    reason: str = ""


class CrawlResult(BaseModel):
    success: bool
    partial: bool
    content_type: str
    text: Optional[str] = None
    images: list[str] = Field(default_factory=list)
    videos: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    extracted_fields: dict = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    telemetry: dict = Field(default_factory=dict)


class CrawlJob(BaseModel):
    """실행 단위 Job. DB row와 1:1 매핑."""

    model_config = ConfigDict(validate_assignment=True)

    id: Optional[int] = None
    url: str
    engine: str
    content_type: Optional[str] = None
    state: JobState = JobState.QUEUED
    retry_count: int = 0
    error_msg: Optional[str] = None
    brain_used: Optional[str] = None
    strategy: CrawlStrategy
    result: Optional[CrawlResult] = None
    partial: bool = False
    duration_ms: Optional[int] = None

    def transition_to(self, new_state: JobState) -> None:
        allowed = ALLOWED_TRANSITIONS.get(self.state, set())
        if new_state not in allowed:
            raise ValueError(
                f"Invalid transition: {self.state.value} -> {new_state.value}"
            )
        self.state = new_state

    def resolve_partial_success(self) -> None:
        """PARTIAL_SUCCESS → mandatory_fields 기준으로 COMPLETED/FAILED 결정."""
        if self.state != JobState.PARTIAL_SUCCESS:
            raise ValueError(f"Job is not in PARTIAL_SUCCESS (current: {self.state})")
        if not self.result:
            raise ValueError("CrawlResult required to resolve partial success")

        mandatory = self.strategy.mandatory_fields
        if not mandatory:
            self.transition_to(JobState.COMPLETED)
        elif all(f in self.result.extracted_fields for f in mandatory):
            self.transition_to(JobState.COMPLETED)
        else:
            self.transition_to(JobState.FAILED)
