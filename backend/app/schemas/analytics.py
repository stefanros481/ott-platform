"""Pydantic schemas for analytics events and content analytics query API."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AnalyticsEventCreate(BaseModel):
    """Request body for POST /api/v1/analytics/events."""

    event_type: Literal["play_start", "play_pause", "play_complete", "browse", "search"]
    title_id: uuid.UUID | None = None
    service_type: Literal["Linear", "VoD", "SVoD", "TSTV", "Catch_up", "Cloud_PVR"]
    profile_id: uuid.UUID | None = None
    region: str
    occurred_at: datetime
    session_id: uuid.UUID | None = None
    duration_seconds: int | None = None
    watch_percentage: int | None = Field(None, ge=0, le=100)
    extra_data: dict | None = None


class QueryRequest(BaseModel):
    """Request body for POST /api/v1/content-analytics/query."""

    question: str = Field(..., min_length=3, max_length=1000)


class QueryResult(BaseModel):
    """Structured result returned by the query engine."""

    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    data: list[dict]
    applied_filters: dict
    data_sources: list[str]
    data_freshness: datetime
    coverage_start: datetime


class ClarificationResponse(BaseModel):
    """Response when the agent cannot determine query intent."""

    type: Literal["clarification"] = "clarification"
    clarifying_question: str
    context: str


class QueryResponse(BaseModel):
    """Union response for POST /api/v1/content-analytics/query."""

    status: Literal["complete", "pending", "clarification"]
    result: QueryResult | None = None
    job_id: uuid.UUID | None = None
    clarification: ClarificationResponse | None = None


class JobStatusResponse(BaseModel):
    """Response for GET /api/v1/content-analytics/jobs/{job_id}."""

    job_id: uuid.UUID
    status: Literal["pending", "complete", "failed"]
    submitted_at: datetime
    completed_at: datetime | None = None
    result: QueryResult | None = None
    error_message: str | None = None
