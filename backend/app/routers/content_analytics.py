"""Content analytics router — natural language query agent."""

import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlalchemy import select

from app.dependencies import AdminUser, DB
from app.models.analytics import QueryJob
from app.schemas.analytics import (
    ClarificationResponse,
    JobStatusResponse,
    QueryRequest,
    QueryResponse,
    QueryResult,
)
from app.services import analytics_service
from app.services.query_engine import (
    classify_complexity,
    create_and_schedule_job,
    extract_parameters,
    match_template,
    resolve_query,
)

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def submit_query(
    body: QueryRequest,
    user: AdminUser,
    db: DB,
    background_tasks: BackgroundTasks,
) -> QueryResponse:
    """Submit a natural language question to the content analytics agent.

    Returns one of:
    - status="complete" with a QueryResult (synchronous path, <2s)
    - status="pending" with a job_id (async path, poll /jobs/{job_id})
    - status="clarification" with a clarifying question (ambiguous input)
    """
    from app.services.analytics_service import NoDataError

    resolution = resolve_query(body.question)

    # Clarification or out-of-domain
    if isinstance(resolution, ClarificationResponse):
        return QueryResponse(status="clarification", clarification=resolution)

    template, params, score = resolution
    is_complex = classify_complexity(template, params)

    if is_complex:
        # Async path: return job_id immediately
        job = await create_and_schedule_job(
            db, user.id, body.question, template, params, score, background_tasks
        )
        return QueryResponse(status="pending", job_id=job.id)

    # Synchronous path: execute and return result directly
    try:
        result = await analytics_service.execute_template_query(db, template, params, score)
        return QueryResponse(status="complete", result=result)
    except NoDataError as exc:
        # Return empty result with explanation rather than an error
        coverage_start, data_freshness = await analytics_service.get_data_coverage(db)
        empty_result = QueryResult(
            summary=f"No data available for {exc.filter_description}.",
            confidence=min(1.0, max(0.0, score)),
            data=[],
            applied_filters={
                "regions": params.regions,
                "time_period": params.time_period,
                "service_type": params.service_type,
            },
            data_sources=["analytics_events"],
            data_freshness=data_freshness,
            coverage_start=coverage_start,
        )
        return QueryResponse(status="complete", result=empty_result)


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: uuid.UUID,
    user: AdminUser,
    db: DB,
) -> JobStatusResponse:
    """Poll the status of an async query job.

    Returns 404 if the job does not exist or belongs to another user.
    """
    result = await db.execute(
        select(QueryJob).where(
            QueryJob.id == job_id,
            QueryJob.user_id == user.id,
        )
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query job not found",
        )

    # Parse JSONB result into QueryResult if complete
    parsed_result: QueryResult | None = None
    if job.status == "complete" and job.result:
        try:
            parsed_result = QueryResult.model_validate(job.result)
        except Exception:
            pass

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        submitted_at=job.submitted_at,
        completed_at=job.completed_at,
        result=parsed_result,
        error_message=job.error_message,
    )
