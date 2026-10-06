from __future__ import annotations

import asyncio
import json
import secrets
from uuid import UUID

from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.redis import redis_client
from app.modules.dashboard.cache import overview_cache_key, topic_questions_cache_key
from app.modules.dashboard.model import InterviewTopicStats
from app.modules.dashboard.schemas import DashboardOverviewResponse
from app.modules.interview.InterviewModel import Interview, InterviewStatus
from app.modules.interviewQuestions.model import InterviewQuestion
from app.modules.interviewTopics.interviewTopics import InterviewTopic
from app.shared.logger.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# GET /dashboard/overview — cache (3.1) + DB build
# ---------------------------------------------------------------------------


async def get_dashboard_overview(user_id: UUID | str | int) -> DashboardOverviewResponse:
    """
    Get the dashboard overview for a user.

    Read path: cache first; on miss, stampede-protected rebuild (lock + poll).
    """
    cache_key = overview_cache_key(user_id)

    cached = await redis_client.get(cache_key)
    if cached:
        return DashboardOverviewResponse.model_validate_json(cached)

    # Cache miss — acquire a short-lived lock to prevent a stampede.
    lock_key = f"{cache_key}:lock"
    lock_token = secrets.token_urlsafe(8)
    acquired = await redis_client.set(
        lock_key,
        lock_token,
        nx=True,
        px=settings.DASHBOARD_CACHE_LOCK_TTL_SECONDS * 1000,
    )

    if acquired:
        try:
            overview = _build_dashboard_overview_db(user_id)
            await redis_client.set(
                cache_key,
                overview.model_dump_json(),
                ex=settings.DASHBOARD_CACHE_TTL_SECONDS,
            )
            return overview
        finally:
            await redis_client.delete(lock_key)

    # Another request is rebuilding — poll the cache key with short backoff.
    for _ in range(3):
        await asyncio.sleep(0.08)
        cached = await redis_client.get(cache_key)
        if cached:
            return DashboardOverviewResponse.model_validate_json(cached)

    # Still empty: fall through and compute directly for this request only.
    logger.warning(f"Dashboard overview ({user_id}) stampede-poll exhausted; computing directly")
    return _build_dashboard_overview_db(user_id)


def _get_scored_question_brief(session, question_id: UUID | None) -> dict | None:
    if question_id is None:
        return None
    q = session.execute(select(InterviewQuestion).where(InterviewQuestion.id == question_id)).scalar_one_or_none()
    if q is None:
        return None
    return {
        "id": str(q.id) if q.id else None,
        "question": q.question,
        "average_score": float(q.average_score) if q.average_score is not None else None,
        "feedback": getattr(q, "feedback", None),
    }


def _build_dashboard_overview_db(user_id: UUID | str | int) -> DashboardOverviewResponse:
    """Build the full overview payload from topic_stats + interviews (no cache)."""
    session = SessionLocal()

    try:
        topic_stats = session.execute(
            select(InterviewTopicStats).where(InterviewTopicStats.user_id == user_id)
        ).scalars().all()

        topics_response: list[dict] = []
        for ts in topic_stats:
            best_feedback = None
            if ts.highest_score_interview_topic_id is not None:
                best_topic = session.get(InterviewTopic, ts.highest_score_interview_topic_id)
                best_feedback = best_topic.feedback if best_topic else None

            topics_response.append(
                {
                    "topic": ts.topic,
                    "average_score": float(ts.average_score) if ts.average_score is not None else None,
                    "highest_score": float(ts.highest_score) if ts.highest_score is not None else None,
                    "lowest_score": float(ts.lowest_score) if ts.lowest_score is not None else None,
                    "interview_count": ts.interview_count,
                    "last_assessed_at": ts.last_assessed_at.isoformat() if ts.last_assessed_at else None,
                    "best_feedback": best_feedback,
                    "highest_scored_question": _get_scored_question_brief(
                        session, ts.highest_scored_question_id
                    ),
                    "lowest_scored_question": _get_scored_question_brief(
                        session, ts.lowest_scored_question_id
                    ),
                }
            )

        # Strongest / weakest topic by average_score.
        sorted_topics = sorted(
            topics_response,
            key=lambda t: (t["average_score"] is None, t["average_score"] or 0),
            reverse=True,
        )
        strongest_topic = (
            {"topic": sorted_topics[0]["topic"], "average_score": sorted_topics[0]["average_score"]}
            if sorted_topics
            else None
        )
        weakest_topic = (
            {"topic": sorted_topics[-1]["topic"], "average_score": sorted_topics[-1]["average_score"]}
            if sorted_topics
            else None
        )

        best_interview = _get_best_interview(session, user_id)

        return DashboardOverviewResponse(
            topics=topics_response,
            strongest_topic=strongest_topic,
            weakest_topic=weakest_topic,
            best_interview=best_interview,
        )

    except Exception as exc:
        logger.exception(f"Failed to build dashboard overview for user {user_id}: {exc}")
        raise

    finally:
        session.close()


def _get_best_interview(session, user_id: UUID | str | int) -> dict | None:
    """Highest overall_score completed interview + its strongest/weakest topics."""
    best_int = session.execute(
        select(Interview)
        .where(Interview.user_id == user_id, Interview.status == InterviewStatus.COMPLETED)
        .order_by(Interview.overall_score.desc())
        .limit(1)
    ).scalar_one_or_none()

    if best_int is None:
        return None

    topic_rows = session.execute(
        select(InterviewTopic)
        .where(InterviewTopic.interview_id == best_int.id)
        .order_by(InterviewTopic.average_score.desc())
    ).scalars().all()

    topic_infos = [
        {
            "topic": t.topic,
            "average_score": float(t.average_score) if t.average_score is not None else None,
        }
        for t in topic_rows
    ]

    return {
        "interview_id": str(best_int.id) if best_int.id else None,
        "overall_score": float(best_int.overall_score) if best_int.overall_score is not None else None,
        "title": best_int.title or "",
        "highest_scored_topic": topic_infos[0] if topic_infos else None,
        "lowest_scored_topic": topic_infos[-1] if len(topic_infos) > 1 else None,
    }


# ---------------------------------------------------------------------------
# GET /dashboard/topics/{topic}/questions — cache (3.2) + DB build
# ---------------------------------------------------------------------------


async def get_topic_questions(
    user_id: UUID | str | int,
    topic: str,
    limit: int = 50,
    offset: int = 0,
    sort: str = "recent",
) -> dict:
    """
    Paginated list of a user's interview_questions for one topic, cached per page.

    sort: "recent" (newest interview first) or "score" (average_score desc).
    """
    cache_key = topic_questions_cache_key(user_id, topic, limit, offset, sort)

    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    lock_key = f"{cache_key}:lock"
    lock_token = secrets.token_urlsafe(8)
    acquired = await redis_client.set(
        lock_key,
        lock_token,
        nx=True,
        px=settings.DASHBOARD_CACHE_LOCK_TTL_SECONDS * 1000,
    )

    if acquired:
        try:
            payload = _build_topic_questions_db(user_id, topic, limit, offset, sort)
            await redis_client.set(cache_key, json.dumps(payload), ex=settings.DASHBOARD_CACHE_TTL_SECONDS)
            return payload
        finally:
            await redis_client.delete(lock_key)

    for _ in range(3):
        await asyncio.sleep(0.08)
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

    logger.warning(f"Topic questions ({user_id}/{topic}) stampede-poll exhausted; computing directly")
    return _build_topic_questions_db(user_id, topic, limit, offset, sort)


def _build_topic_questions_db(
    user_id: UUID | str | int,
    topic: str,
    limit: int = 50,
    offset: int = 0,
    sort: str = "recent",
) -> dict:
    session = SessionLocal()

    try:
        where_clause = (
            InterviewQuestion.user_id == user_id,
            InterviewQuestion.category == topic,
        )

        total = session.execute(select(func.count()).select_from(InterviewQuestion).where(*where_clause)).scalar_one()

        stmt = select(InterviewQuestion).where(*where_clause)
        if sort == "score":
            stmt = stmt.order_by(InterviewQuestion.average_score.desc())
        else:
            stmt = stmt.order_by(
                InterviewQuestion.created_at.desc(),
                InterviewQuestion.question_number.asc(),
            )

        rows = session.execute(stmt.offset(offset).limit(limit)).scalars().all()

        questions = [
            {
                "id": str(q.id) if q.id else None,
                "question_number": q.question_number,
                "question": q.question,
                "answer": q.answer,
                "average_score": float(q.average_score) if q.average_score is not None else None,
                "difficulty": q.difficulty.value if q.difficulty else None,
                "strong_concepts": q.strong_concepts or [],
                "weak_concepts": q.weak_concepts or [],
                "feedback": getattr(q, "feedback", None),
            }
            for q in rows
        ]

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "questions": questions,
        }

    except Exception as exc:
        logger.exception(f"Failed to fetch topic questions for user {user_id}, topic {topic}: {exc}")
        raise

    finally:
        session.close()
