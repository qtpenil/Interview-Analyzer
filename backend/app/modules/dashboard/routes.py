from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.modules.dashboard.schemas import DashboardOverviewResponse
from app.modules.dashboard.service import get_dashboard_overview, get_topic_questions
from app.shared.response_handler.responseSchema import SuccessResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/overview",
    response_model=SuccessResponse[DashboardOverviewResponse],
    summary="Get dashboard overview (cached)",
)
async def dashboard_overview(
    current_user_id: str | int = Depends(get_current_user),
) -> SuccessResponse[DashboardOverviewResponse]:
    """
    Get the dashboard overview for the authenticated user.

    Response is cached in Redis under `dashboard:overview:{user_id}`.
    Cache TTL is `DASHBOARD_CACHE_TTL_SECONDS` (default 86400 = 24 hours).
    Stampede protection: concurrent cache-miss requests contend for a short-lived
    lock; the first to acquire rebuilds, others poll until the key populates.

    Invalidation: the Celery task that saves analysis results deletes the cache key
    after persisting the new interview's topic_stats + interview_questions.
    """
    overview = await get_dashboard_overview(current_user_id)
    return SuccessResponse(
        message="Dashboard overview retrieved",
        data=overview,
    )


@router.get(
    "/topics/{topic}/questions",
    summary="Get interview questions for a topic",
)
async def topic_questions(
    topic: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="recent", pattern="^(recent|score)$"),
    current_user_id: str | int = Depends(get_current_user),
) -> SuccessResponse[dict]:
    """
    Get all interview questions for a given user and topic, with pagination.

    - `limit`: max items to return (default 50)
    - `offset`: pagination offset (default 0)
    - `sort`: "recent" (newest first) or "score" (average_score desc)

    Cached per (topic, page, sort) in Redis; invalidated for touched topics
    after a new interview's analysis is persisted.
    """
    result = await get_topic_questions(current_user_id, topic, limit=limit, offset=offset, sort=sort)
    return SuccessResponse(
        message="Topic questions retrieved successfully",
        data=result,
    )
