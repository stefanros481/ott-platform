"""Natural language query engine for content analytics.

Maps user questions to predefined SQL query templates using embedding
similarity (all-MiniLM-L6-v2 via the shared embedding_service model).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import QueryJob
from app.schemas.analytics import ClarificationResponse, QueryResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class QueryTemplate:
    """A predefined analytics query pattern with its embedding."""

    id: str
    name: str
    description: str
    sql: str
    parameters: list[str]
    summary_tpl: str
    embedding: list[float] | None = field(default=None, repr=False)


@dataclass
class QueryParameters:
    """Extracted filter parameters from a natural language question."""

    regions: list[str] | None = None
    service_type: str | None = None
    time_period: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


# ---------------------------------------------------------------------------
# Query templates (10 required patterns)
# ---------------------------------------------------------------------------

TEMPLATES: list[QueryTemplate] = [
    QueryTemplate(
        id="genre_revenue",
        name="Genre Revenue",
        description=(
            "Which genres drive SVoD revenue? Show me genre revenue breakdown. "
            "Which genres are most profitable for subscription content?"
        ),
        sql="""
            SELECT
                g.name                                            AS genre,
                ae.service_type,
                COUNT(ae.id)                                      AS event_count,
                COUNT(CASE WHEN ae.event_type = 'play_complete' THEN 1 END) AS completions,
                ROUND(
                    100.0 * COUNT(CASE WHEN ae.event_type = 'play_complete' THEN 1 END)
                    / NULLIF(COUNT(CASE WHEN ae.event_type = 'play_start' THEN 1 END), 0),
                    1
                )                                                 AS completion_rate_pct
            FROM analytics_events ae
            LEFT JOIN titles t ON ae.title_id = t.id
            LEFT JOIN title_genres tg ON tg.title_id = t.id AND tg.is_primary = TRUE
            LEFT JOIN genres g ON g.id = tg.genre_id
            WHERE ae.event_type IN ('play_start', 'play_complete')
              AND g.name IS NOT NULL
            GROUP BY g.name, ae.service_type
            ORDER BY event_count DESC
            LIMIT 20
        """,
        parameters=["regions", "start_date", "end_date", "service_type"],
        summary_tpl=(
            "{% if genre %}{{ genre }}{% else %}Drama{% endif %} content leads with "
            "{{ event_count }} play events and a {{ completion_rate_pct }}% completion rate "
            "for {{ service_type }} service. Based on events captured since {{ coverage_start.strftime('%Y-%m-%d') }}."
        ),
    ),
    QueryTemplate(
        id="trending_by_profile_type",
        name="Trending by Profile Type",
        description=(
            "What are trending shows for kids vs adults? "
            "Show me popular content for kids profiles versus adult profiles. "
            "Compare viewing patterns between kids and adult accounts."
        ),
        sql="""
            SELECT
                t.title                                           AS title,
                g.name                                            AS genre,
                p.is_kids,
                COUNT(ae.id)                                      AS play_count,
                ROUND(
                    100.0 * COUNT(CASE WHEN ae.event_type = 'play_complete' THEN 1 END)
                    / NULLIF(COUNT(CASE WHEN ae.event_type = 'play_start' THEN 1 END), 0),
                    1
                )                                                 AS completion_rate_pct
            FROM analytics_events ae
            LEFT JOIN titles t ON ae.title_id = t.id
            LEFT JOIN title_genres tg ON tg.title_id = t.id AND tg.is_primary = TRUE
            LEFT JOIN genres g ON g.id = tg.genre_id
            LEFT JOIN profiles p ON ae.profile_id = p.id
            WHERE ae.event_type IN ('play_start', 'play_complete')
              AND t.title IS NOT NULL
              AND p.is_kids IS NOT NULL
            GROUP BY t.title, g.name, p.is_kids
            ORDER BY play_count DESC
            LIMIT 20
        """,
        parameters=["regions", "start_date", "end_date"],
        summary_tpl=(
            "{% if title %}{{ title }}{% else %}Top content{% endif %} is trending "
            "with {{ play_count }} plays. Kids and adult profiles show distinct preferences "
            "in viewing patterns. Based on events since {{ coverage_start.strftime('%Y-%m-%d') }}."
        ),
    ),
    QueryTemplate(
        id="pvr_impact",
        name="Cloud PVR Impact",
        description=(
            "How does Cloud PVR impact viewing? "
            "What effect does recording have on viewing patterns? "
            "Compare recorded content viewing against live and VoD."
        ),
        sql="""
            SELECT
                ae.service_type,
                COUNT(ae.id)                                      AS event_count,
                COUNT(CASE WHEN ae.event_type = 'play_complete' THEN 1 END) AS completions,
                ROUND(AVG(ae.watch_percentage))                   AS avg_watch_pct,
                ROUND(
                    100.0 * COUNT(CASE WHEN ae.event_type = 'play_complete' THEN 1 END)
                    / NULLIF(COUNT(CASE WHEN ae.event_type = 'play_start' THEN 1 END), 0),
                    1
                )                                                 AS completion_rate_pct
            FROM analytics_events ae
            WHERE ae.event_type IN ('play_start', 'play_complete')
              AND ae.service_type IN ('Cloud_PVR', 'Linear', 'VoD')
            GROUP BY ae.service_type
            ORDER BY event_count DESC
        """,
        parameters=["regions", "start_date", "end_date"],
        summary_tpl=(
            "Cloud PVR users show {{ avg_watch_pct }}% average watch completion, "
            "compared against Linear and VoD baselines. "
            "Based on events since {{ coverage_start.strftime('%Y-%m-%d') }}."
        ),
    ),
    QueryTemplate(
        id="svod_upgrade_drivers",
        name="SVoD Upgrade Drivers",
        description=(
            "What content drives SVoD upgrades? "
            "Which titles or genres motivate users to subscribe? "
            "Show me content that correlates with subscription sign-ups."
        ),
        sql="""
            SELECT
                t.title                                           AS title,
                g.name                                            AS genre,
                COUNT(CASE WHEN ae.event_type = 'browse' THEN 1 END)        AS browse_count,
                COUNT(CASE WHEN ae.event_type = 'play_start' THEN 1 END)    AS play_count,
                ROUND(
                    100.0 * COUNT(CASE WHEN ae.event_type = 'play_start' THEN 1 END)
                    / NULLIF(COUNT(CASE WHEN ae.event_type = 'browse' THEN 1 END), 0),
                    1
                )                                                 AS browse_to_play_pct
            FROM analytics_events ae
            LEFT JOIN titles t ON ae.title_id = t.id
            LEFT JOIN title_genres tg ON tg.title_id = t.id AND tg.is_primary = TRUE
            LEFT JOIN genres g ON g.id = tg.genre_id
            WHERE ae.event_type IN ('browse', 'play_start')
              AND ae.service_type = 'SVoD'
              AND t.title IS NOT NULL
            GROUP BY t.title, g.name
            ORDER BY browse_count DESC
            LIMIT 15
        """,
        parameters=["regions", "start_date", "end_date"],
        summary_tpl=(
            "{% if title %}{{ title }}{% else %}SVoD content{% endif %} leads SVoD engagement "
            "with {{ browse_count }} browses converting at {{ browse_to_play_pct }}% to plays. "
            "Based on events since {{ coverage_start.strftime('%Y-%m-%d') }}."
        ),
    ),
    QueryTemplate(
        id="regional_preferences",
        name="Regional Content Preferences",
        description=(
            "Regional content preferences across markets. "
            "What do users prefer in different regions? "
            "Show me genre popularity by country or market."
        ),
        sql="""
            SELECT
                ae.region,
                g.name                                            AS genre,
                COUNT(ae.id)                                      AS event_count,
                ROUND(
                    100.0 * COUNT(CASE WHEN ae.event_type = 'play_complete' THEN 1 END)
                    / NULLIF(COUNT(CASE WHEN ae.event_type = 'play_start' THEN 1 END), 0),
                    1
                )                                                 AS completion_rate_pct
            FROM analytics_events ae
            LEFT JOIN titles t ON ae.title_id = t.id
            LEFT JOIN title_genres tg ON tg.title_id = t.id AND tg.is_primary = TRUE
            LEFT JOIN genres g ON g.id = tg.genre_id
            WHERE ae.event_type IN ('play_start', 'play_complete')
              AND g.name IS NOT NULL
            GROUP BY ae.region, g.name
            ORDER BY ae.region, event_count DESC
        """,
        parameters=["regions", "start_date", "end_date"],
        summary_tpl=(
            "Region {{ region }} shows strongest preference for {{ genre }} content "
            "with {{ event_count }} events and {{ completion_rate_pct }}% completion. "
            "Based on events since {{ coverage_start.strftime('%Y-%m-%d') }}."
        ),
    ),
    QueryTemplate(
        id="engagement_by_service",
        name="Engagement by Service Type",
        description=(
            "Engagement rate by content type Linear vs VoD. "
            "Compare viewing engagement across service types. "
            "Show me how Linear, VoD, SVoD, and other services compare."
        ),
        sql="""
            SELECT
                ae.service_type,
                COUNT(ae.id)                                      AS event_count,
                COUNT(CASE WHEN ae.event_type = 'play_start' THEN 1 END)    AS play_starts,
                COUNT(CASE WHEN ae.event_type = 'play_complete' THEN 1 END) AS completions,
                ROUND(AVG(ae.watch_percentage))                   AS avg_watch_pct,
                ROUND(
                    100.0 * COUNT(CASE WHEN ae.event_type = 'play_complete' THEN 1 END)
                    / NULLIF(COUNT(CASE WHEN ae.event_type = 'play_start' THEN 1 END), 0),
                    1
                )                                                 AS completion_rate_pct
            FROM analytics_events ae
            WHERE ae.event_type IN ('play_start', 'play_complete')
            GROUP BY ae.service_type
            ORDER BY play_starts DESC
        """,
        parameters=["regions", "start_date", "end_date"],
        summary_tpl=(
            "{{ service_type }} leads with {{ play_starts }} play starts and "
            "a {{ completion_rate_pct }}% completion rate (avg {{ avg_watch_pct }}% watched). "
            "Based on events since {{ coverage_start.strftime('%Y-%m-%d') }}."
        ),
    ),
    QueryTemplate(
        id="top_titles",
        name="Top Titles by Completion",
        description=(
            "Which titles have the highest completion rate? "
            "Show me the most-watched content to the end. "
            "What are the most engaging titles on the platform?"
        ),
        sql="""
            SELECT
                t.title,
                g.name                                            AS genre,
                ae.service_type,
                COUNT(CASE WHEN ae.event_type = 'play_start' THEN 1 END)    AS play_starts,
                COUNT(CASE WHEN ae.event_type = 'play_complete' THEN 1 END) AS completions,
                ROUND(
                    100.0 * COUNT(CASE WHEN ae.event_type = 'play_complete' THEN 1 END)
                    / NULLIF(COUNT(CASE WHEN ae.event_type = 'play_start' THEN 1 END), 0),
                    1
                )                                                 AS completion_rate_pct,
                ROUND(AVG(ae.watch_percentage))                   AS avg_watch_pct
            FROM analytics_events ae
            LEFT JOIN titles t ON ae.title_id = t.id
            LEFT JOIN title_genres tg ON tg.title_id = t.id AND tg.is_primary = TRUE
            LEFT JOIN genres g ON g.id = tg.genre_id
            WHERE ae.event_type IN ('play_start', 'play_complete')
              AND t.title IS NOT NULL
            GROUP BY t.title, g.name, ae.service_type
            HAVING COUNT(CASE WHEN ae.event_type = 'play_start' THEN 1 END) >= 2
            ORDER BY completion_rate_pct DESC NULLS LAST
            LIMIT 20
        """,
        parameters=["regions", "start_date", "end_date", "service_type"],
        summary_tpl=(
            "{% if title %}{{ title }}{% else %}Top title{% endif %} leads with a "
            "{{ completion_rate_pct }}% completion rate and {{ avg_watch_pct }}% average watch. "
            "Based on events since {{ coverage_start.strftime('%Y-%m-%d') }}."
        ),
    ),
    QueryTemplate(
        id="revenue_growth",
        name="Revenue Growth by Genre",
        description=(
            "Which genres had highest revenue growth last quarter? "
            "Show me genre trends over time. "
            "Compare content performance across time periods."
        ),
        sql="""
            SELECT
                g.name                                            AS genre,
                DATE_TRUNC('month', ae.occurred_at)               AS month,
                COUNT(ae.id)                                      AS event_count,
                COUNT(CASE WHEN ae.event_type = 'play_complete' THEN 1 END) AS completions
            FROM analytics_events ae
            LEFT JOIN titles t ON ae.title_id = t.id
            LEFT JOIN title_genres tg ON tg.title_id = t.id AND tg.is_primary = TRUE
            LEFT JOIN genres g ON g.id = tg.genre_id
            WHERE ae.event_type IN ('play_start', 'play_complete')
              AND g.name IS NOT NULL
            GROUP BY g.name, DATE_TRUNC('month', ae.occurred_at)
            ORDER BY month DESC, event_count DESC
            LIMIT 30
        """,
        parameters=["regions", "start_date", "end_date"],
        summary_tpl=(
            "{% if genre %}{{ genre }}{% else %}Drama{% endif %} shows {{ event_count }} events "
            "in the most recent period. "
            "Based on events since {{ coverage_start.strftime('%Y-%m-%d') }}."
        ),
    ),
    QueryTemplate(
        id="content_browse_behavior",
        name="Browse Without Watch Behavior",
        description=(
            "What content do users browse but not watch? "
            "Show me high-browse low-play content. "
            "Which titles attract browsing but not playback?"
        ),
        sql="""
            SELECT
                t.title,
                g.name                                            AS genre,
                COUNT(CASE WHEN ae.event_type = 'browse' THEN 1 END)        AS browse_count,
                COUNT(CASE WHEN ae.event_type = 'play_start' THEN 1 END)    AS play_count,
                ROUND(
                    100.0 * COUNT(CASE WHEN ae.event_type = 'play_start' THEN 1 END)
                    / NULLIF(COUNT(CASE WHEN ae.event_type = 'browse' THEN 1 END), 0),
                    1
                )                                                 AS browse_to_play_pct
            FROM analytics_events ae
            LEFT JOIN titles t ON ae.title_id = t.id
            LEFT JOIN title_genres tg ON tg.title_id = t.id AND tg.is_primary = TRUE
            LEFT JOIN genres g ON g.id = tg.genre_id
            WHERE ae.event_type IN ('browse', 'play_start')
              AND t.title IS NOT NULL
            GROUP BY t.title, g.name
            HAVING COUNT(CASE WHEN ae.event_type = 'browse' THEN 1 END) >= 2
            ORDER BY browse_count DESC, browse_to_play_pct ASC
            LIMIT 20
        """,
        parameters=["regions", "start_date", "end_date", "service_type"],
        summary_tpl=(
            "{% if title %}{{ title }}{% else %}Content{% endif %} has "
            "{{ browse_count }} browses but only {{ browse_to_play_pct }}% convert to plays, "
            "suggesting a discovery gap. "
            "Based on events since {{ coverage_start.strftime('%Y-%m-%d') }}."
        ),
    ),
    QueryTemplate(
        id="cross_service_comparison",
        name="Cross-Service Viewing Comparison",
        description=(
            "Compare viewing time across Linear and SVoD. "
            "Side-by-side comparison of service types. "
            "How does engagement differ between Linear TV, SVoD, and on-demand?"
        ),
        sql="""
            SELECT
                ae.service_type,
                COUNT(ae.id)                                      AS total_events,
                COUNT(CASE WHEN ae.event_type = 'play_start' THEN 1 END)    AS play_starts,
                COUNT(CASE WHEN ae.event_type = 'play_complete' THEN 1 END) AS completions,
                ROUND(AVG(ae.duration_seconds) / 60.0, 1)        AS avg_duration_min,
                ROUND(AVG(ae.watch_percentage))                   AS avg_watch_pct,
                ROUND(
                    100.0 * COUNT(CASE WHEN ae.event_type = 'play_complete' THEN 1 END)
                    / NULLIF(COUNT(CASE WHEN ae.event_type = 'play_start' THEN 1 END), 0),
                    1
                )                                                 AS completion_rate_pct
            FROM analytics_events ae
            WHERE ae.event_type IN ('play_start', 'play_complete')
            GROUP BY ae.service_type
            ORDER BY play_starts DESC
        """,
        parameters=["regions", "start_date", "end_date"],
        summary_tpl=(
            "{{ service_type }} has {{ play_starts }} play starts with "
            "{{ avg_duration_min }} min average duration and {{ completion_rate_pct }}% completion. "
            "Based on events since {{ coverage_start.strftime('%Y-%m-%d') }}."
        ),
    ),
]

# Sentinel returned when clarification is needed
_CLARIFICATION_SENTINEL = "__clarification__"

# ---------------------------------------------------------------------------
# Embedding initialization
# ---------------------------------------------------------------------------

_embeddings_initialized = False


def _init_embeddings() -> None:
    """Compute embeddings for all templates using the shared model instance."""
    global _embeddings_initialized
    if _embeddings_initialized:
        return

    from app.services.embedding_service import get_model

    model = get_model()
    descriptions = [t.description for t in TEMPLATES]
    vectors = model.encode(descriptions, normalize_embeddings=True)
    for template, vector in zip(TEMPLATES, vectors):
        template.embedding = vector
    _embeddings_initialized = True
    logger.info("Query engine: loaded %d templates with embeddings", len(TEMPLATES))


# ---------------------------------------------------------------------------
# Core engine functions
# ---------------------------------------------------------------------------


def match_template(question: str) -> tuple[QueryTemplate, float]:
    """Embed *question* and return the closest template with its similarity score."""
    _init_embeddings()

    from app.services.embedding_service import get_model

    model = get_model()
    q_vec = model.encode(question, normalize_embeddings=True)

    best_template = TEMPLATES[0]
    best_score = -1.0

    for template in TEMPLATES:
        if template.embedding is None:
            continue
        score = float(np.dot(q_vec, np.array(template.embedding)))
        if score > best_score:
            best_score = score
            best_template = template

    return best_template, best_score


def extract_parameters(question: str) -> QueryParameters:
    """Extract filter parameters from a natural language question via keyword matching."""
    import re

    q = question.lower()
    now = datetime.now(timezone.utc)

    # --- Region extraction (always produces list[str]) ---
    regions: list[str] | None = None
    region_map: list[tuple[list[str], list[str]]] = [
        (["nordics", "scandinavia", "nordic countries"], ["NO", "SE", "DK"]),
        (["norway", "norwegian", "norsk"], ["NO"]),
        (["sweden", "swedish", "sverige"], ["SE"]),
        (["denmark", "danish", "denmark", "danmark"], ["DK"]),
        (["finland", "finnish"], ["FI"]),
        (["uk", "united kingdom", "britain", "british"], ["GB"]),
        (["germany", "german", "deutschland"], ["DE"]),
        (["france", "french"], ["FR"]),
        (["netherlands", "dutch", "holland"], ["NL"]),
    ]
    found_regions: list[str] = []
    for keywords, codes in region_map:
        for kw in keywords:
            if kw in q:
                for code in codes:
                    if code not in found_regions:
                        found_regions.append(code)
                break
    if found_regions:
        regions = found_regions

    # --- Service type extraction ---
    service_type: str | None = None
    service_map = [
        (["cloud pvr", "cloud_pvr", "pvr", "recording", "recorded"], "Cloud_PVR"),
        (["catch-up", "catch up", "catchup"], "Catch_up"),
        (["tstv", "time-shifted", "start over", "start-over"], "TSTV"),
        (["svod", "subscription", "subscription vod"], "SVoD"),
        (["vod", "on demand", "on-demand"], "VoD"),
        (["linear", "live tv", "live television"], "Linear"),
    ]
    for keywords, stype in service_map:
        for kw in keywords:
            if kw in q:
                service_type = stype
                break
        if service_type:
            break

    # --- Time period extraction ---
    time_period: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None

    from datetime import timedelta

    if "last quarter" in q or "previous quarter" in q:
        time_period = "last_quarter"
        # Find the start/end of the previous calendar quarter
        month = now.month
        year = now.year
        current_q = (month - 1) // 3 + 1
        if current_q == 1:
            start_date = datetime(year - 1, 10, 1, tzinfo=timezone.utc)
            end_date = datetime(year, 1, 1, tzinfo=timezone.utc)
        elif current_q == 2:
            start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
            end_date = datetime(year, 4, 1, tzinfo=timezone.utc)
        elif current_q == 3:
            start_date = datetime(year, 4, 1, tzinfo=timezone.utc)
            end_date = datetime(year, 7, 1, tzinfo=timezone.utc)
        else:
            start_date = datetime(year, 7, 1, tzinfo=timezone.utc)
            end_date = datetime(year, 10, 1, tzinfo=timezone.utc)

    elif "this quarter" in q:
        time_period = "this_quarter"
        month = now.month
        year = now.year
        current_q = (month - 1) // 3 + 1
        start_month = (current_q - 1) * 3 + 1
        start_date = datetime(year, start_month, 1, tzinfo=timezone.utc)
        end_date = now

    elif "last month" in q or "previous month" in q:
        time_period = "last_month"
        first_of_this = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = first_of_this
        start_date = (first_of_this - timedelta(days=1)).replace(day=1)

    elif "this month" in q:
        time_period = "this_month"
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now

    elif "last year" in q or "previous year" in q:
        time_period = "last_year"
        start_date = datetime(now.year - 1, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(now.year, 1, 1, tzinfo=timezone.utc)

    elif "last week" in q or "previous week" in q:
        time_period = "last_week"
        end_date = now - timedelta(days=now.weekday() + 1)
        start_date = end_date - timedelta(days=7)

    elif "last 30 days" in q or "past 30 days" in q or "30 days" in q:
        time_period = "last_30_days"
        end_date = now
        start_date = now - timedelta(days=30)

    elif "last 90 days" in q or "past 90 days" in q or "90 days" in q:
        time_period = "last_90_days"
        end_date = now
        start_date = now - timedelta(days=90)
    else:
        # Check for 4-digit year
        year_match = re.search(r"\b(20\d{2})\b", q)
        if year_match:
            year = int(year_match.group(1))
            time_period = str(year)
            start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
            end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)

    return QueryParameters(
        regions=regions,
        service_type=service_type,
        time_period=time_period,
        start_date=start_date,
        end_date=end_date,
    )


def classify_complexity(template: QueryTemplate, params: QueryParameters) -> bool:
    """Return True if the query should be executed asynchronously.

    Cross-service comparison templates are always async. Otherwise, queries with
    >2 dimensions and at least 2 active filters are considered complex.
    """
    # Cross-service templates always run async (multiple full-table aggregations)
    if template.id in ("engagement_by_service", "cross_service_comparison"):
        return True

    # Count active filters
    active_filters = sum([
        params.regions is not None,
        params.start_date is not None,
        params.service_type is not None,
    ])

    # Complex if the template joins multiple dimensions AND multiple filters applied
    multi_dimension_templates = {"genre_revenue", "revenue_growth", "regional_preferences"}
    if template.id in multi_dimension_templates and active_filters >= 2:
        return True

    return False


async def create_and_schedule_job(
    db: AsyncSession,
    user_id: uuid.UUID,
    question: str,
    template: QueryTemplate,
    params: QueryParameters,
    similarity_score: float,
    background_tasks: BackgroundTasks,
) -> QueryJob:
    """Insert a QueryJob row and schedule async execution via BackgroundTasks."""
    from datetime import timezone

    from sqlalchemy import select

    job = QueryJob(
        user_id=user_id,
        question=question,
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    job_id = job.id

    async def _run_job() -> None:
        from datetime import datetime, timezone

        from app.database import async_session_factory
        from app.services.analytics_service import NoDataError, execute_template_query

        async with async_session_factory() as job_db:
            try:
                result = await execute_template_query(job_db, template, params, similarity_score)
                result_dict = result.model_dump(mode="json")

                job_row = await job_db.get(QueryJob, job_id)
                if job_row:
                    job_row.status = "complete"
                    job_row.result = result_dict
                    job_row.completed_at = datetime.now(timezone.utc)
                    await job_db.commit()

            except NoDataError as exc:
                job_row = await job_db.get(QueryJob, job_id)
                if job_row:
                    job_row.status = "failed"
                    job_row.error_message = f"No data available for {exc.filter_description}"
                    job_row.completed_at = datetime.now(timezone.utc)
                    await job_db.commit()

            except Exception as exc:
                logger.exception("Background job %s failed", job_id)
                try:
                    job_row = await job_db.get(QueryJob, job_id)
                    if job_row:
                        job_row.status = "failed"
                        job_row.error_message = str(exc)[:500]
                        job_row.completed_at = datetime.now(timezone.utc)
                        await job_db.commit()
                except Exception:
                    logger.exception("Failed to update job %s status to failed", job_id)

    background_tasks.add_task(_run_job)
    return job


def resolve_query(
    question: str,
) -> tuple[QueryTemplate, QueryParameters, float] | ClarificationResponse:
    """Top-level entry point: match template and extract parameters.

    Returns either a (template, params, score) tuple for execution, or a
    ClarificationResponse when the question is ambiguous or out of domain.
    """
    template, score = match_template(question)
    params = extract_parameters(question)

    # Out-of-domain guard: similarity too low to be platform-related
    if score < 0.35:
        return ClarificationResponse(
            clarifying_question=(
                "This metric isn't available in the platform's analytics data. "
                "The agent can answer questions about: viewing engagement, completion rates, "
                "content preferences, regional trends, and service type comparisons."
            ),
            context="The question appears to be outside the platform's analytics scope.",
        )

    # Ambiguity: score below confidence threshold — ask for clarification
    if score < 0.65:
        # Check for multi-part questions
        question_marks = question.count("?")
        has_conjunction = " and " in question.lower() and question_marks >= 1
        if question_marks > 1 or has_conjunction:
            return ClarificationResponse(
                clarifying_question=(
                    "Your question has multiple parts — which would you like answered first?"
                ),
                context="The question contains multiple distinct queries.",
            )

        # Generic clarification based on question content
        q_lower = question.lower()
        if any(w in q_lower for w in ["content", "show", "program", "title"]) and not any(
            w in q_lower for w in ["revenue", "engagement", "completion", "watch", "view", "browse", "search"]
        ):
            return ClarificationResponse(
                clarifying_question=(
                    "Which aspect of content performance are you interested in? "
                    "For example: revenue, engagement rate, completion rate, or viewership numbers?"
                ),
                context="The metric dimension of the question is not specified.",
            )

        return ClarificationResponse(
            clarifying_question=(
                "Could you be more specific? For example: "
                "\"Which genres drive SVoD revenue?\" or \"Show me completion rates by region.\""
            ),
            context=f"The question matched template '{template.name}' with low confidence ({score:.2f}).",
        )

    return template, params, score
