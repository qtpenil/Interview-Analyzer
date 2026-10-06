# pyrefly: ignore [missing-import]
from datetime import timedelta
from functools import cached_property
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    SECRET_KEY: str
    ALGORITHM: str

    COOKIE_SECURE: bool
    COOKIE_HTTPONLY: bool
    COOKIE_SAMESITE: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    VERIFICATION_TOKEN_EXPIRE_MINUTES: int

    BROKER_URL: str

    CORS_ORIGINS: list[str]
    REDIS_DATA_EXPIRE: int

    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"
    # if someone forgets to add them in .env, the application still works.
    SILENCE_NOISE_THRESHOLD: str = "-35dB"
    SILENCE_MIN_DURATION: int = 10
    GROQ_API_KEY: str

    # Email / SMTP Config
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""

    REDIS_URL: str = "redis://localhost:6379/0"

    QUESTION_BATCH_SIZE: int = 15

    # API Keys
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEYS: str

    LLM_CONCURRENCY_LIMIT: int = 5

    # LLM Models
    OLLAMA_MODEL: str = "llama3"
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    GOOGLE_AI_MODEL: str = "gemini-1.5-flash"

    # Ollama Baae Url
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Storage Configuration (Local)
    STORAGE_DIR: str = "storage"

    # ---------------------------------------------------------------------------
    # Hardening pipeline additions
    # ---------------------------------------------------------------------------
    # Phase 1 Config
    LLM_TIMEOUT_SECONDS: int = 180
    INITIAL_RETRY_DELAY: float = 1.0
    BACKOFF_MULTIPLIER: float = 2.0
    MAX_RETRY_DELAY: float = 10.0
    MAX_RETRIES: int = 3
    ENABLE_RETRY_JITTER: bool = True
    ENABLE_PROVIDER_FALLBACK: bool = True
    PRIMARY_PROVIDER: str = "google"
    FALLBACK_PROVIDER: str = "openai"
    OPENAI_API_KEYS: str = ""
    ANTHROPIC_API_KEYS: str = ""

    # Phase 2 Config
    MAX_CONCURRENT_INTERVIEWS: int = 5
    MAX_CONCURRENT_LLM_REQUESTS: int = 10
    QUEUE_WAIT_TIMEOUT: float = 60.0
    CONCURRENCY_BACKEND: str = "local"  # "local" | "redis"

    # Phase 6 Config
    ENABLE_CHECKPOINTING: bool = True

    # Phase 7 & 8 Config
    ENABLE_PII_REDACTION: bool = False
    ENABLE_PROMPT_SANITIZATION: bool = True
    MAX_TRANSCRIPT_SIZE: int = 100000  # characters
    MAX_TRANSCRIPT_DURATION: float = 7200.0  # seconds (2 hours)
    MAX_PROMPT_TOKENS: int = 32000
    ON_LIMIT_EXCEEDED: str = "reject"  # "split" | "reject"

    # Audio prep modes for transcription: default/trimmed, raw, silence_aware
    AUDIO_PREP_MODE: str = "trimmed"

    # Dashboard analytics caching (Part 3)
    DASHBOARD_CACHE_TTL_SECONDS: int = 86400  # safety-net expiry; invalidation is the primary refresh mechanism
    DASHBOARD_CACHE_LOCK_TTL_SECONDS: int = 10  # stampede-protection lock hold time

    @property
    def DATABASE_URL(self):
        password = quote_plus(self.DB_PASSWORD)
        return f"postgresql+psycopg2://{self.DB_USER}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @cached_property
    def TOKEN_CONFIG(self):
        return {
            "access": {
                "cookie_name": "access_token",
                "expiry": timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES).total_seconds(),
            },
            "refresh": {
                "cookie_name": "refresh_token",
                "expiry": timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds(),
            },
            "verification": {
                "cookie_name": "verification_token",
                "expiry": timedelta(minutes=self.VERIFICATION_TOKEN_EXPIRE_MINUTES).total_seconds(),
            },
        }

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
