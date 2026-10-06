import json
import uuid
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.rate_limiter import limiter
from app.core.security import get_current_user
from app.main import create_app
from app.modules.dashboard.model import InterviewTopicStats
from app.modules.interviewQuestions.model import InterviewQuestion
from app.modules.interviewTopics.interviewTopics import InterviewTopic


class _Result:
    def __init__(self, rows=None, scalar=None):
        self._rows = rows or []
        self._scalar = scalar

    def scalars(self):
        return self

    def all(self):
        return self._rows

    def scalar_one(self):
        return self._scalar

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None


class FakeSession:
    """Minimal SQLAlchemy-session stand-in dispatching on the select's entity."""

    def __init__(self, rows=None, gets=None, count=0):
        self.rows = rows or {}
        self.gets = gets or {}
        self.count = count
        self.closed = False

    def execute(self, stmt):
        descriptions = stmt.column_descriptions
        entity = descriptions[0]["entity"] if descriptions else None
        if entity is None:  # select(func.count()).select_from(...)
            return _Result(scalar=self.count)
        return _Result(rows=self.rows.get(entity, []))

    def get(self, model, ident):
        return self.gets.get((model, ident))

    def close(self):
        self.closed = True


@pytest.fixture
def app():
    application = create_app()
    limiter.enabled = False
    application.dependency_overrides[get_current_user] = lambda: str(uuid.uuid4())
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
def dash_redis():
    mock = AsyncMock()
    mock.get.return_value = None
    with patch("app.modules.dashboard.service.redis_client", mock):
        yield mock


def _overview_cache_json(**overrides) -> str:
    payload = {
        "topics": [],
        "strongest_topic": None,
        "weakest_topic": None,
        "best_interview": None,
    }
    payload.update(overrides)
    return json.dumps(payload)


def _fake_overview_components():
    stats = SimpleNamespace(
        topic="Python",
        average_score=Decimal("8.00"),
        highest_score=Decimal("9.00"),
        lowest_score=Decimal("7.00"),
        interview_count=2,
        last_assessed_at=datetime(2026, 9, 9, 12, 0, 0),
        highest_score_interview_topic_id=uuid.uuid4(),
        lowest_scored_question_id=None,
        highest_scored_question_id=uuid.uuid4(),
    )
    topic = SimpleNamespace(feedback="Great depth")
    question = SimpleNamespace(
        id=stats.highest_scored_question_id,
        question="Explain generators",
        average_score=Decimal("9.00"),
        feedback="concise",
    )
    from app.modules.interview.InterviewModel import Interview

    session = FakeSession(
        rows={
            InterviewTopicStats: [stats],
            InterviewQuestion: [question],
            Interview: [],
            InterviewTopic: [],
        },
        gets={(InterviewTopic, stats.highest_score_interview_topic_id): topic},
    )
    return stats, session


async def _get_client(app):
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_overview_requires_auth():
    application = create_app()
    limiter.enabled = False
    async with await _get_client(application) as client:
        resp = await client.get("/dashboard/overview")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_overview_cache_hit_skips_db(app, dash_redis):
    cached = _overview_cache_json(topics=[{"topic": "Python", "average_score": 8.0}])
    dash_redis.get.return_value = cached

    with patch("app.modules.dashboard.service.SessionLocal") as mock_session_local:
        async with await _get_client(app) as client:
            resp = await client.get("/dashboard/overview")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["topics"][0]["topic"] == "Python"
    mock_session_local.assert_not_called()


@pytest.mark.asyncio
async def test_overview_cache_miss_builds_and_caches(app, dash_redis):
    _, fake_session = _fake_overview_components()

    with patch("app.modules.dashboard.service.SessionLocal", return_value=fake_session):
        async with await _get_client(app) as client:
            resp = await client.get("/dashboard/overview")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["topics"][0]["topic"] == "Python"
    assert data["topics"][0]["average_score"] == "8.0"  # Decimal serializes to string
    assert data["topics"][0]["best_feedback"] == "Great depth"
    assert data["topics"][0]["highest_scored_question"]["question"] == "Explain generators"
    assert fake_session.closed

    dash_redis.set.assert_awaited()  # once for the stampede lock, once for the cache
    assert dash_redis.set.await_count == 2
    cache_set = dash_redis.set.await_args_list[1]
    key, payload = cache_set.args[0], cache_set.args[1]
    assert key.startswith("dashboard:overview:")
    assert json.loads(payload)["topics"][0]["topic"] == "Python"


@pytest.mark.asyncio
async def test_overview_stampede_poll_wins(app, dash_redis):
    cached = _overview_cache_json(topics=[{"topic": "Python", "average_score": 8.0}])
    dash_redis.set.return_value = False  # lock held by another request
    dash_redis.get.side_effect = [None, cached, cached, cached]

    with patch("app.modules.dashboard.service._build_dashboard_overview_db") as builder:
        builder.return_value = None
        async with await _get_client(app) as client:
            resp = await client.get("/dashboard/overview")

    assert resp.status_code == 200
    assert resp.json()["data"]["topics"][0]["topic"] == "Python"
    builder.assert_not_called()
    dash_redis.set.await_args.kwargs["nx"] is True


@pytest.mark.asyncio
async def test_overview_stampede_poll_exhausted_computes_directly(app, dash_redis):
    from app.modules.dashboard.schemas import DashboardOverviewResponse

    empty_overview = DashboardOverviewResponse()
    dash_redis.set.return_value = False
    dash_redis.get.side_effect = [None, None, None, None]

    with (
        patch("app.modules.dashboard.service.SessionLocal", return_value=FakeSession()),
        patch(
            "app.modules.dashboard.service._build_dashboard_overview_db",
            return_value=empty_overview,
        ) as builder,
    ):
        async with await _get_client(app) as client:
            resp = await client.get("/dashboard/overview")

    assert resp.status_code == 200
    builder.assert_called_once()


def _example_question(qnum: int, score: float) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        question_number=qnum,
        question=f"Q{qnum}?",
        answer=f"A{qnum}",
        average_score=Decimal(str(score)),
        difficulty=SimpleNamespace(value="medium"),
        strong_concepts=["c1"],
        weak_concepts=[],
        feedback=f"fb{qnum}",
    )


@pytest.mark.asyncio
async def test_topic_questions_invalid_sort_rejected(app):
    async with await _get_client(app) as client:
        resp = await client.get("/dashboard/topics/Python/questions?sort=bogus")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_topic_questions_recent_default(app, dash_redis):
    questions = [_example_question(1, 7.0), _example_question(2, 9.0)]
    fake_session = FakeSession(rows={InterviewQuestion: questions}, count=len(questions))

    with patch("app.modules.dashboard.service.SessionLocal", return_value=fake_session):
        async with await _get_client(app) as client:
            resp = await client.get("/dashboard/topics/Python/questions")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 2
    assert len(data["questions"]) == 2
    assert data["questions"][0]["question_number"] == 1
    assert fake_session.closed

    key = dash_redis.set.call_args.args[0]
    assert key.startswith("dashboard:topic_questions:")
    assert key.endswith(":50:0:recent")


@pytest.mark.asyncio
async def test_topic_questions_score_sort_caches_per_page(app, dash_redis):
    captured = {}

    def fake_builder(user_id, topic, limit, offset, sort):
        captured["sort"] = sort
        return {"total": 0, "limit": limit, "offset": offset, "questions": []}

    with patch("app.modules.dashboard.service._build_topic_questions_db", side_effect=fake_builder):
        async with await _get_client(app) as client:
            resp = await client.get("/dashboard/topics/Python/questions?sort=score&limit=10&offset=20")

    assert resp.status_code == 200
    assert captured["sort"] == "score"
    key = dash_redis.set.call_args.args[0]
    assert ":10:20:score" in key
