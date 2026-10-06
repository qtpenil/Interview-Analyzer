import asyncio
import os
import sys
import time
import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Mock pydub before any app module imports it (pyaudioop not
# available in this Python 3.13 test environment).
from unittest.mock import MagicMock as _Mock
sys.modules.setdefault("pydub", _Mock())
sys.modules.setdefault("pydub.AudioSegment", _Mock())

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Ensure project root is on sys.path so "app" module is importable
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

os.environ.setdefault("ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("GEMINI_API_KEYS", "fake-key-1,fake-key-2")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "root")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "ai_interview_test")
os.environ.setdefault("COOKIE_SECURE", "False")
os.environ.setdefault("COOKIE_HTTPONLY", "True")
os.environ.setdefault("COOKIE_SAMESITE", "lax")
os.environ.setdefault("VERIFICATION_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("REDIS_DATA_EXPIRE", "3600")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("BROKER_URL", "redis://localhost:6379/1")
os.environ.setdefault("FFMPEG_PATH", "ffmpeg")
os.environ.setdefault("FFPROBE_PATH", "ffprobe")
os.environ.setdefault("STORAGE_DIR", "storage")
os.environ.setdefault("SMTP_HOST", "smtp.test.local")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_USER", "test@test.local")
os.environ.setdefault("SMTP_PASSWORD", "test-password")
os.environ.setdefault("FROM_EMAIL", "test@test.local")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:3000"]')
os.environ.setdefault("ENABLE_CHECKPOINTING", "False")
os.environ.setdefault("CONCURRENCY_BACKEND", "local")
os.environ.setdefault("LLM_CONCURRENCY_LIMIT", "5")
os.environ.setdefault("MAX_RETRIES", "1")
os.environ.setdefault("ENABLE_PROVIDER_FALLBACK", "False")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-fake")
os.environ.setdefault("GROQ_API_KEY", "gsk_fake_test_key")

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import create_app

TEST_DATABASE_URL = settings.DATABASE_URL


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()
    TestSession = sessionmaker(bind=connection)
    session = TestSession()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def override_get_db(db_session: Session):
    def _override():
        yield db_session

    return _override


@pytest.fixture
def app(override_get_db) -> FastAPI:
    from app.core.rate_limiter import limiter

    application = create_app()
    application.dependency_overrides[get_db] = override_get_db
    # Disable rate limiting globally in tests — @limiter.limit() wraps endpoints
    # INLINE, so app.state.limiter is irrelevant. We must flip the flag on the
    # singleton limiter instance directly.
    limiter.enabled = False
    return application


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


_last_register_time: float = 0.0


@pytest.fixture
def respect_rate_limit():
    global _last_register_time
    elapsed = time.time() - _last_register_time
    if elapsed < 13:
        time.sleep(13 - elapsed)
    _last_register_time = time.time()
    yield


@pytest.fixture
async def auth_cookies(async_client):
    """Register and login a fresh user. Returns httpx Cookies."""
    email = f"auth_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPass@123"
    reg_resp = await async_client.post(
        "/auth/register",
        json={
            "name": f"u_{uuid.uuid4().hex[:2]}",
            "email": email,
            "password": password,
        },
    )
    assert reg_resp.status_code in (200, 201), f"Register failed: {reg_resp.status_code}"
    login_resp = await async_client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.status_code}"
    return login_resp.cookies


@pytest.fixture
def sample_password() -> str:
    return "TestPass@123"


@pytest.fixture
def sample_user_data(sample_password) -> dict:
    return {
        "name": f"t_{uuid.uuid4().hex[:2]}",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": sample_password,
    }


@pytest.fixture(autouse=True)
def _reset_lazy_redis():
    from app.core.redis import redis_client

    redis_client._client = None
    yield
    redis_client._client = None


@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    mock.get.return_value = None
    mock.setex.return_value = True
    with (
        patch("app.core.redis.redis_client", mock),
        patch("app.modules.auth.authService.redis_client", mock),
        patch("app.core.security.redis_client", mock),
    ):
        yield mock



@pytest.fixture
def mock_gemini():
    with patch("app.integration.transcription.manager.genai") as mock:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "test transcription"
        mock.Client.return_value = mock_client
        yield mock


@pytest.fixture
def mock_ffmpeg():
    """Mock subprocess.run for FFmpeg operations."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"format": {"duration": 120.0}}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        yield mock_run


@pytest.fixture
def mock_fpcalc():
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"fingerprint": "test_fingerprint_123"}'
        mock_run.return_value = mock_result
        yield mock_run


@pytest.fixture
def mock_celery_task():
    task = MagicMock()
    task.retry = MagicMock(side_effect=Exception("Retry triggered"))
    return task


@pytest.fixture
def mock_smtp():
    with patch("smtplib.SMTP") as mock:
        smtp_instance = MagicMock()
        mock.return_value.__enter__.return_value = smtp_instance
        yield smtp_instance


@pytest.fixture
def sample_video_path(tmp_path) -> str:
    video_file = tmp_path / "test_video.mp4"
    video_file.write_bytes(b"fake video content")
    return str(video_file)


@pytest.fixture
def sample_audio_path(tmp_path) -> str:
    audio_file = tmp_path / "test_audio.wav"
    audio_file.write_bytes(b"fake audio content")
    return str(audio_file)


@pytest.fixture
def sample_transcript_segments() -> list[dict]:
    return [
        {"start": 0.0, "end": 5.0, "text": "Hello, welcome to the interview."},
        {"start": 5.0, "end": 10.0, "text": "I have five years of experience in software development."},
        {"start": 10.0, "end": 15.0, "text": "My primary skills include Python and cloud architecture."},
    ]


@pytest.fixture
def sample_state_dict() -> dict:
    return {
        "interview_id": str(uuid.uuid4()),
        "candidate_name": "John Doe",
        "claimed_experience_years": 5.0,
        "hiring_decision": "HIRE",
        "overall_score": 8.5,
        "technical_score": 8.0,
        "communication_score": 7.5,
        "confidence_score": 9.0,
        "knowledge_depth": 8.0,
        "experience_alignment_score": 7.0,
        "summary": "Strong candidate with solid technical background.",
        "final_feedback": "Recommended for hire.",
        "strengths": ["Technical depth", "Communication"],
        "weaknesses": ["Could improve system design"],
        "risk_factors": [],
        "interview_summary": {
            "candidate_name": "John Doe",
            "hiring_decision": "HIRE",
            "overall_score": 8.5,
        },
        "question_evaluations": [{"question": "Explain Python decorators", "score": 8.0, "category": "python"}],
        "topics": [
            {
                "topic": "Python",
                "average_score": 8.5,
                "confidence_score": 9.0,
                "strongest_concepts": ["Decorators", "Generators"],
                "weakest_concepts": ["AsyncIO"],
            }
        ],
        "questions": [{"question": "Explain Python decorators", "answer": "A decorator is a function..."}],
    }
