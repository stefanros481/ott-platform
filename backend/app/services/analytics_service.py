"""Service layer for analytics event ingestion and query execution."""

import logging
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AnalyticsEvent
from app.schemas.analytics import AnalyticsEventCreate, QueryResult

logger = logging.getLogger(__name__)


class NoDataError(Exception):
    """Raised when a filtered query returns zero rows."""

    def __init__(self, filter_description: str) -> None:
        self.filter_description = filter_description
        super().__init__(filter_description)


async def ingest_event(
    db: AsyncSession,
    user_id: uuid.UUID,
    payload: AnalyticsEventCreate,
) -> AnalyticsEvent:
    """Persist a single analytics event to the database."""
    event = AnalyticsEvent(
        event_type=payload.event_type,
        title_id=payload.title_id,
        service_type=payload.service_type,
        user_id=user_id,
        profile_id=payload.profile_id,
        region=payload.region,
        occurred_at=payload.occurred_at,
        session_id=payload.session_id,
        duration_seconds=payload.duration_seconds,
        watch_percentage=payload.watch_percentage,
        extra_data=payload.extra_data,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def get_data_coverage(db: AsyncSession) -> tuple[datetime, datetime]:
    """Return (MIN(occurred_at), MAX(occurred_at)) from analytics_events.

    Falls back to utcnow() for both values when the table is empty.
    """
    result = await db.execute(
        text("SELECT MIN(occurred_at), MAX(occurred_at) FROM analytics_events")
    )
    row = result.one()
    now = datetime.now(timezone.utc)
    coverage_start = row[0] if row[0] is not None else now
    data_freshness = row[1] if row[1] is not None else now
    return coverage_start, data_freshness


async def execute_template_query(
    db: AsyncSession,
    template: "QueryTemplate",  # type: ignore[name-defined]  # noqa: F821
    params: "QueryParameters",  # type: ignore[name-defined]  # noqa: F821
    similarity_score: float,
) -> QueryResult:
    """Execute the parameterized SQL from *template* with *params*.

    Builds WHERE clauses for region, time period, and service type filters.
    Renders the Jinja2 summary template from top result values.
    Raises NoDataError when the filtered result set is empty.
    """
    from jinja2 import Template

    from app.services.query_engine import QueryParameters, QueryTemplate

    # Determine data sources: titles JOIN means both tables contribute
    data_sources = ["analytics_events"]
    if "titles" in template.sql.lower():
        data_sources.append("titles")

    # Build WHERE clauses for filters — use the 'ae' alias used in all templates
    where_clauses: list[str] = []
    bind_params: dict = {}

    if params.regions:
        where_clauses.append("ae.region = ANY(:regions)")
        bind_params["regions"] = params.regions

    if params.start_date:
        where_clauses.append("ae.occurred_at >= :start_date")
        where_clauses.append("ae.occurred_at < :end_date")
        bind_params["start_date"] = params.start_date
        bind_params["end_date"] = params.end_date

    if params.service_type:
        where_clauses.append("ae.service_type = :service_type")
        bind_params["service_type"] = params.service_type

    # Inject filters into the SQL before GROUP BY/ORDER BY/LIMIT so the clauses
    # appear in a valid position (not after LIMIT).
    sql = template.sql
    if where_clauses:
        filter_sql = "\n              AND " + "\n              AND ".join(where_clauses)
        # Find the position of GROUP BY, ORDER BY, or LIMIT (whichever comes first)
        match = re.search(r"\b(GROUP\s+BY|ORDER\s+BY|LIMIT)\b", sql, re.IGNORECASE)
        if match:
            insert_pos = match.start()
            sql = sql[:insert_pos] + filter_sql + "\n            " + sql[insert_pos:]
        elif re.search(r"\bWHERE\b", sql, re.IGNORECASE):
            sql = sql.rstrip() + filter_sql
        else:
            sql = sql.rstrip() + "\n            WHERE 1=1" + filter_sql

    try:
        result = await db.execute(text(sql).bindparams(**bind_params))
        rows = result.mappings().all()
    except Exception as exc:
        logger.exception("Template query failed for template=%s", template.id)
        raise exc

    coverage_start, data_freshness = await get_data_coverage(db)

    if not rows:
        filter_parts = []
        if params.regions:
            filter_parts.append(f"region={params.regions}")
        if params.start_date:
            filter_parts.append(f"time_period={params.time_period}")
        if params.service_type:
            filter_parts.append(f"service_type={params.service_type}")
        filter_description = ", ".join(filter_parts) if filter_parts else "applied filters"
        raise NoDataError(filter_description)

    # Render Jinja2 summary template with top result
    top = dict(rows[0])
    try:
        summary = Template(template.summary_tpl).render(**top, coverage_start=coverage_start)
    except Exception:
        summary = f"Query results for {template.name}."

    # Build applied_filters dict
    applied_filters = {
        "regions": params.regions,
        "time_period": params.time_period,
        "service_type": params.service_type,
    }
    if params.regions is None:
        summary = summary + " Results cover all regions."

    return QueryResult(
        summary=summary,
        confidence=min(1.0, max(0.0, similarity_score)),
        data=[dict(r) for r in rows],
        applied_filters=applied_filters,
        data_sources=data_sources,
        data_freshness=data_freshness,
        coverage_start=coverage_start,
    )
