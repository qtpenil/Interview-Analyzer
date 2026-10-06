# Interview AI — Backend

FastAPI + Celery backend for **Interview AI**: upload an interview video, and the system transcribes it, analyzes the candidate's answers with an LLM, and produces a scored assessment report (PDF).

The API returns immediately after upload; everything heavy (audio cleaning, transcription, AI analysis, PDF generation) runs asynchronously through a Celery pipeline, with status tracked on the `interviews` record and exposed via a polling endpoint.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [The Interview Processing Pipeline](#the-interview-processing-pipeline)
5. [Modules](#modules)
6. [Database Schema](#database-schema)
7. [API Reference](#api-reference)
8. [Response & Error Formats](#response--error-formats)
9. [Configuration (.env)](#configuration-env)
10. [Setup & Running](#setup--running)
11. [Testing](#testing)
12. [Quality Tooling](#quality-tooling)
13. [Documentation](#documentation)

---

## Architecture Overview

```
                 upload video                  dispatch task (Redis broker)
┌────────┐  ────────────────▶ ┌──────────────────┐ ────────────────▶ ┌──────────────────┐
│Client  │                    │ FastAPI (Uvicorn)│                    │  Celery Worker   │
└────────┘  ◀──────────────── └──────────────────┘ ◀───────────────── └────────┬─────────┘
  status polling /                returns interview_id                         │ pipeline
  report download (S3 or local)                                     ┌──────────┴──────────┐
                                                                    ▼                     ▼
                                             1. Video → cleaned WAV           2. Transcription
                                                    (ffmpeg)              (Gemini, chunked +
                                                                          parallel, key rotation)
                                                                    │                     │
                                                                    ▼                     ▼
                                                               3. LangGraph analysis
                                                                  (5-node LLM pipeline)
                                                                    │
                                                                    ▼
                                             4. PDF report (ReportLab) → S3 + File row
```

Key idea: **the HTTP layer only does fast things** (save video, create DB row, dispatch a Celery task). All slow/expensive work — ffmpeg, LLM calls, PDF rendering — happens inside Celery workers, so the API stays responsive. The pipeline is retryable, resumable (checkpoints), and cancellable by the user.

Infrastructure:

- **PostgreSQL** — primary data store and the Celery result backend (`db+postgresql://...`).
- **Redis** — rate-limiter storage, OTP/verification-token storage, optional distributed concurrency gates and LangGraph checkpoints.
- **Broker** — any Celery broker (Redis/RabbitMQ) via `BROKER_URL`.
- **Storage** — hosts the final PDF reports in `/app/storage/reports/`; intermediate files (uploaded video, cleaned WAV) live in a local `storage/` dir and are deleted after use.

---

## Tech Stack

| Concern | Technology |
|---|---|
| API framework | FastAPI 0.136, Uvicorn |
| Async task queue | Celery 5.6 (Redis broker, `db+postgres` result backend) |
| Database / ORM | PostgreSQL 17, SQLAlchemy 2.0, psycopg2 |
| Migrations | Alembic |
| Cache / rate limit / OTP | Redis (`redis-py` async) |
| Auth | JWT (PyJWT) in httpOnly cookies, pwdlib/argon2 password hashing |
| Media processing | ffmpeg / ffprobe (subprocess), pydub |
| Transcription | Google Gemini (`google-genai`), chunked + parallel with API-key rotation |
| LLM orchestration | LangGraph 1.2, LangChain structured output, provider strategy (Google / OpenAI / Anthropic / Ollama) |
| PDF reports | ReportLab |
| Duplicate detection | Chromaprint (`fpcalc`) audio fingerprints |
| Storage | Local Filesystem / Docker Volume (`storage_data`) |
| Email | SMTP (smtplib, HTML OTP email as Celery task) |
| Quality | ruff, mypy, pytest, pre-commit |

---

## Project Structure

```
app/
├── main.py                        # FastAPI app factory: CORS, routes, exception handlers, lifespan
├── celery_app.py                  # Celery app: broker, db result backend, task imports, hard limits
├── core/
│   ├── config.py                  # pydantic-settings — every env var lives here
│   ├── database.py                # SQLAlchemy engine (pooling), SessionLocal, get_db()
│   ├── security.py                # JWT encode/decode, password hashing, OTP, get_current_user dep
│   ├── rate_limiter.py            # slowapi Limiter bound to Redis
│   └── redis.py                   # async Redis client wrapper (lazy)
├── modules/
│   ├── auth/                      # register / login / logout / refresh / forgot-password flow
│   │   ├── authRoutes.py
│   │   ├── authService.py
│   │   └── authSchema.py
│   ├── user/                      # User + OTP SQLAlchemy models
│   ├── interview/                 # upload, status, cancel, detail, list, report download
│   │   ├── routes.py              # all /interviews endpoints
│   │   ├── service.py             # DB operations, duplicate check, file save
│   │   ├── schemas.py             # response Pydantic schemas
│   │   ├── InterviewModel.py      # Interview ORM model + status/decision enums
│   │   └── interview_media_service.py  # video → silence-removed WAV orchestration
│   ├── files/                     # File ORM model (videos, PDFs) + FileType enum
│   └── interviewTopics/           # InterviewTopic ORM model (per-topic scores)
├── tasks/                         # Celery pipeline tasks
│   ├── video_tasks.py             # step 1: validate + extract audio + dedupe check
│   ├── transcription_tasks.py     # step 2: chunked Gemini transcription + interview classifier
│   ├── analysis_tasks.py          # step 3: LangGraph analysis
│   ├── pdf_tasks.py               # step 4: PDF generation + S3 upload + COMPLETED
│   └── email_tasks.py             # OTP email sender
├── integration/
│   ├── ffmpeg/                    # command builders, manager, silence parsing, fingerprinting
│   ├── transcription/             # Gemini transcription manager + utils (chunking, dedupe)
│   ├── langGraph/                 # 5-node LangGraph assessment pipeline + hardening layer
│   ├── pdf/                       # ReportLab report generator
│   └── interview_classifier/      # Gemini heuristic: "is this actually an interview?"
└── shared/
    ├── exceptions/                # custom exception classes + FastAPI handlers
    ├── response_handler/          # SuccessResponse envelope + auth cookie helpers
    ├── db/status_updater.py       # Celery-safe DB updates (own sessions)
    ├── logger/                    # console + rotating file logging
    └── storage/                   # S3 client + upload/download/presign helpers
```

Tests live in `tests/` (unit tests for utils, managers, tasks, services, models, graph, and API-level tests in `tests/api/`). Database migrations live in `alembic/versions/`.

---

## The Interview Processing Pipeline

The pipeline is a chain of **4 Celery tasks** that hand control to each other via `.delay()`:

### Step 1 — `process_video_to_audio` (`app/tasks/video_tasks.py`)

Dispatcher: `POST /interviews/upload` saves the video to `storage/uploads/` and starts this task.

1. Aborts early if the interview was cancelled (`is_interview_cancelled`).
2. Validates duration via ffprobe: **must be 60 s – 2 h**; otherwise marks `FAILED` with `failure_reason`.
3. Sets status `PROCESSING` and converts video → cleaned mono 16 kHz WAV:
   - `ffmpeg` extracts the audio track (16-bit PCM, 16 kHz, mono, high-pass/low-pass/denoise/normalization filters);
   - `silencedetect` finds long silences (≥ 10 s below −35 dB);
   - non-silent intervals are extracted and concatenated back into a single `storage/whisper/<uuid>.wav`;
   - the original video file is deleted.
4. **Duplicate detection**: computes a Chromaprint fingerprint of a 120 s sample (from the 5-minute mark) with `fpcalc`. If a *completed* interview with the same fingerprint exists for the same user:
   - copies transcript + all scored fields + topic rows onto the new record,
   - reuses the original checkpoint to generate the PDF directly,
   - skips transcription and analysis entirely (returns `status: "duplicate"`).
5. Otherwise chains to `transcribe_audio`.

### Step 2 — `transcribe_audio` (`app/tasks/transcription_tasks.py`)

1. Sets status `TRANSCRIBING`.
2. `TranscriptionManager` splits the WAV into 5-minute chunks (20 s overlap, max 20 chunks, auto-enlarged for longer audio), transcribes them **in parallel** (ThreadPoolExecutor, up to 4 workers) using Gemini with a strict "never hallucinate" prompt (`temperature=0`).
3. API keys are round-robin across chunks; each failing chunk retries on **every key in the pool** before failing loudly.
4. Chunks are merged with **word-level fuzzy deduplication** of the overlapping text, normalized, and split into sentence-aware segments; timestamps are interpolated from a character-index timeline to prevent drift.
5. Transcript segments are saved to `Interview.transcript` (JSONB), the WAV is cleaned up.
6. **Interview classifier**: Gemini decides whether the transcript is actually an interview; if not, the interview is marked `FAILED` ("Uploaded video does not appear to be an interview").
7. Otherwise chains to `analyze_transcript`.

### Step 3 — `analyze_transcript` (`app/tasks/analysis_tasks.py`)

1. Sets status `ANALYZING`.
2. Runs the **LangGraph pipeline** (`InterviewGraphRunner`), which is coordinted with:
   - an **idempotency check** (returns cached results if already `COMPLETED`),
   - a **concurrency gate** (max concurrent interviews, configurable),
   - **transcript preprocessing** (Unicode NFC, input validation, size/duration limits, optional PII redaction),
   - **resume support**: if `ENABLE_CHECKPOINTING` and a checkpoint exists, failed nodes are reset to `PENDING` and the graph resumes from the checkpoint.
3. After the graph completes, results are saved to the DB (`save_interview_analysis_results`) and PDF generation is queued.

### Step 4 — `generate_pdf_report` (`app/tasks/pdf_tasks.py`)

1. Renders the report with ReportLab (`InterviewPDFService`).
2. Saves the PDF locally at `storage/reports/interview/<id>/interview-report.pdf` (`save_file`).
3. Creates/updates the `File` row (`file_type = SUMMARY_PDF`, `storage_provider = "local"`).
4. Sets status `COMPLETED` with `processing_completed_at`.

### Failure & cancellation handling

- Every task has `max_retries`; after exhausting retries the interview is marked `FAILED`. `failure_reason` is saved where meaningful.
- Each task checks `is_interview_cancelled()` up front; `POST /interviews/{id}/cancel` (only valid for `UPLOADED`/`PROCESSING`/`TRANSCRIBING`/`ANALYZING`) flips the status and all in-flight tasks bail out and clean up temp files.
- Hard Celery limits: `task_time_limit=3600`, `task_soft_time_limit=3540`, result expiry 1 day.

### Status lifecycle

```
UPLOADED → PROCESSING → TRANSCRIBING → ANALYZING → COMPLETED
    │            │            │            │
    └────────────┴────────────┴────────────┴──▶ FAILED (after retries exhausted / rejected input)
    │            │            │            │
    └────────────┴────────────┴────────────┴──▶ CANCELLED (user-initiated, mid-pipeline)
```

---

## Modules

### Core (`app/core`)

- **config.py** — Pydantic `Settings` loaded from `.env`. Everything from DB credentials to LLM API keys, timeouts, concurrency limits, and pipeline hardening knobs (see [Configuration](#configuration-env)). Also builds the SQLAlchemy `DATABASE_URL` (password URL-encoded) and a `TOKEN_CONFIG` map (access / refresh / verification cookies with expiry).
- **database.py** — SQLAlchemy engine with a connection pool (`pool_size=20`, `max_overflow=10`, `pool_pre_ping`), `Base` for all models, `SessionLocal` factory, and the `get_db` FastAPI dependency.
- **security.py** — JWT creation/decoding, argon2 password hashing (pwdlib `PasswordHash.recommended()`), 6-digit OTP generator, password-strength validator (`PasswordStr`), and the `get_current_user` dependency that reads the `access_token` **cookie** (JWT claims `sub` is the user id). Verification tokens are also stored in Redis (`verify:<token> → email`) so `update-password` can resolve the email without a DB round-trip.
- **rate_limiter.py** — slowapi `Limiter` with Redis storage, keyed on remote address.
- **redis.py** — lazy async Redis client wrapper (connects on first use).

### Auth (`app/modules/auth`) + User (`app/modules/user`)

Cookie-based JWT auth. Tokens are set as httpOnly cookies (`access_token`, `refresh_token`, and `verification_token` for password reset) via `set_auth_cookie`; `get_current_user` reads the cookie on every protected route.

| Endpoint | What happens |
|---|---|
| `POST /auth/register` | Validates (name 3–5 chars, email, strong password), hashes password, inserts user, issues access+refresh cookies. Rate-limited 5/min. |
| `POST /auth/login` | Verifies credentials, issues access+refresh cookies. Rate-limited 5/min. |
| `POST /auth/logout` | Clears both auth cookies (client cannot clear httpOnly cookies itself). |
| `POST /auth/refreshToken` | Decodes the refresh cookie (must have `token_type: "refresh"`), issues a new access cookie. |
| `POST /auth/forgot-password` | Generates an OTP, stores it in Redis (`otp:<email>`, TTL from `REDIS_DATA_EXPIRE`), and sends a themed HTML email via `send_otp_email` Celery task. |
| `POST /auth/resend-otp` | Same, but with a 30 s Redis cooldown per email. |
| `POST /auth/verify-otp` | Compares OTP against Redis, deletes it, mints a one-time `verification_token` (stored in Redis + cookie). |
| `POST /auth/update-password` | Requires the `verification_token` cookie; resolves the email, updates the hash, clears the cookie. |

Users table stores email / password hash / name. (An `otps` table exists in the schema as a fallback but the live flow uses Redis.)

### Interview (`app/modules/interview`)

The heart of the API — see [API Reference](#api-reference) for endpoints. Notable details:

- `POST /upload` saves the video locally, creates the `Interview` row (`UPLOADED`), creates a `File` row (`VIDEO`, local provider), dispatches `process_video_to_audio`, and returns `interview_id` + `status` inside the standard `data` envelope.
- `service.py` also implements `cancel_interview` (with file cleanup), `get_interview_report_path` (local file first, S3 fallback), `list_interviews_for_user` (paginated, excludes `CANCELLED`, fills missing titles from the video filename), and `check_duplicate_interview` (fingerprint + user, only matches `COMPLETED` interviews).
- `interview_media_service.py` orchestrates the ffmpeg steps region above.

### Files & Topics (`app/modules/files`, `app/modules/interviewTopics`)

- `File` rows track every artifact per interview: the uploaded video (`VIDEO`, local) and the generated report (`SUMMARY_PDF`, S3). Fields: `file_type`, `storage_provider`, `storage_path`, `file_size`.
- `InterviewTopic` rows store per-topic results after analysis: topic name, `average_score`, `confidence_score`, `strongest_concepts` / `weakest_concepts` (JSONB), and `feedback`. Unique per `(interview_id, topic)`.

### Integration Layer (`app/integration`)

- **ffmpeg/** — Pure command builders (`commands.py`), the `FFmpegManager` (safe `subprocess.run` wrappers that raise typed exceptions), and utilities: `parse_silence_output`, `build_keep_intervals`, `generate_audio_fingerprint` (fpcalc + ffmpeg trim).
- **transcription/** — `TranscriptionManager` (chunking, parallel Gemini calls, key rotation, dedupe merge, timestamp interpolation) and utils (`split_audio_to_memory`, `find_overlap_length`, `deduplicate_overlapping_text`, `normalize_text`, `split_into_segments`).
- **interview_classifier/** — Small Gemini JSON call that classifies a transcript as an interview or not (fail-open if no keys/errors).
- **langGraph/** — The AI assessment brain (details below).
- **pdf/** — `InterviewPDFService`: a polished multi-page ReportLab report (decision badge, score bars, topic overview + detail cards, per-question pages with score grids, summary). Carefully engineered to avoid ReportLab `LayoutError` (no huge content in tables, `LongText` paragraph style for long prose).

#### The LangGraph pipeline (`app/integration/langGraph`)

A compiled `StateGraph` with 5 sequential nodes sharing a typed `InterviewGraphState` (TypedDict + Pydantic schemas):

1. **transcript_structuring** — turns raw timed segments into typed `ConversationBlock`s (speaker role/label + text), validated by `outputValidator` (2 attempts).
2. **metadata_qa_extractor** — one LLM call extracts candidate metadata (name, claimed experience, current/target role, intro summary) **and** all question-answer pairs (with follow-ups).
3. **batched_qa_assessment** — evaluates Q&A pairs in batches of `QUESTION_BATCH_SIZE` (default 15). Each evaluation (`QuestionEvaluation`) carries per-question scores (accuracy, depth, completeness, clarity, confidence, experience alignment), strong/missing concepts, strengths/weaknesses and feedback.
4. **topic_aggregation** — fully **deterministic** (no LLM): buckets evaluations by category, averages scores, computes top strong/weak concepts by frequency, generates rule-based feedback templates.
5. **interview_summary** — computes the six headline scores deterministically from question metrics, then asks the LLM to write qualitative feedback (strengths, weaknesses, risk factors, final feedback, hiring decision). The LLM's numeric claims are **overwritten with the deterministic values** before saving.

Hardening layer around the graph:

- **retryManager.py** — `invoke_structured` runs `ChatPromptTemplate | model.with_structured_output(schema)` with: per-attempt timeout (`LLM_TIMEOUT_SECONDS`), exponential backoff + jitter, **API-key rotation** on transient failures (KeyRotator per provider), and **provider fallback** (primary Google, fallback OpenAI/Anthropic) — only providers in `ACTIVE_PROVIDERS` with configured keys are attempted.
- **provider_strategy.py** — `Provider` ABC with OpenAI / Anthropic / Google / Ollama strategies; `provider_manager` resolves by name.
- **concurrency.py** — distributed semaphores via Redis Lua scripts (or a local threading/fork-safe backend) gating *interviews* (`MAX_CONCURRENT_INTERVIEWS`) and *LLM requests* (`MAX_CONCURRENT_LLM_REQUESTS`); also stores LangGraph **checkpoints** (serialized state with `__type__` markers) for resume-after-crash.
- **security_hardening.py** — `preprocess_transcript`: Unicode NFC, per-segment validation (malformed segments are skipped but > 5 % malformed fails loudly), size/duration caps (`MAX_TRANSCRIPT_SIZE`, `MAX_TRANSCRIPT_DURATION`, `ON_LIMIT_EXCEEDED` ∈ reject/truncate), optional PII redaction (email/SSN/phone regexes).
- **outputValidator.py** — Pydantic + business-rule validation of every node's output; failed validation triggers the attempt loop.

### Background Tasks (`app/tasks`)

| Task | Purpose |
|---|---|
| `process_video_to_audio` | Step 1 (see pipeline): duration checks, audio cleaning, fingerprint + dedupe, chain. |
| `transcribe_audio` | Step 2: Gemini transcription, classifier gate, chain. |
| `analyze_transcript` | Step 3: LangGraph run, persist results, chain to PDF. |
| `generate_pdf_report` | Step 4: ReportLab → S3 → `File` row → `COMPLETED`. |
| `send_otp_email` | SMTP delivery of the password-reset OTP (retries with 30 s countdown). |

### Shared (`app/shared`)

- **exceptions/** — `AppException` base with `status_code`/`error_code`, typed subclasses (auth, OTP, rate limit, ffmpeg, file upload, etc.), and FastAPI handlers returning the `ErrorResponse` envelope. Registered in `main.py`.
- **response_handler/** — `SuccessResponse` envelope: `{success, message, data, meta}` (see [Response formats](#response--error-formats)). `response_cookie_setter.py` handles auth cookie setting/clearing using `TOKEN_CONFIG`.
- **db/status_updater.py** — Celery-safe DB helpers that open their **own** sessions (never FastAPI's DI session): `update_interview_status`, `update_interview_fields`, `is_interview_cancelled`, `save_interview_analysis_results`.
- **logger/** — console + rotating file handler (`logs/application.log`, 10 MB × 5 backups), a fixed line format, configured at startup and per worker.
- **storage/** — Local storage service with `save_file`, `read_file`, `download_fileobj`, `download_file`, `delete_file`, `generate_presigned_url`.

---

## Database Schema

Tables (managed by Alembic, all PostgreSQL-specific UUID/JSONB):

**users**
| Column | Notes |
|---|---|
| id | UUID PK |
| email | unique, indexed |
| password_hash | argon2 |
| name | optional |
| created_at / updated_at | server defaults |

**interviews**
| Column | Notes |
|---|---|
| id | UUID PK |
| user_id | FK users (cascade delete), indexed |
| title | optional |
| claimed_experience_years | Numeric(4,1) |
| overall / technical / communication / confidence / knowledge_depth / experience_alignment_score | Numeric(5,2), nullable |
| hiring_decision | enum: STRONG_HIRE / HIRE / BORDERLINE / NO_HIRE |
| status | enum: UPLOADED / PROCESSING / TRANSCRIBING / ANALYZING / COMPLETED / FAILED / CANCELLED, indexed |
| ai_model_name / ai_model_version | who did the analysis |
| transcript | JSONB (timed segments) |
| audio_fingerprint | Text (chromaprint) |
| failure_reason | Text |
| processing_started_at / processing_completed_at | timestamps |
| created_at / updated_at | |

**interview_topics**
| Column | Notes |
|---|---|
| id | UUID PK |
| interview_id | FK interviews (cascade) |
| topic | String, unique with interview_id (`uq_interview_topic`) |
| average_score / confidence_score | Numeric(5,2) |
| strongest_concepts / weakest_concepts | JSONB |
| feedback | Text |

**files**
| Column | Notes |
|---|---|
| id | UUID PK |
| interview_id | FK interviews (cascade), indexed |
| file_type | enum VIDEO / SUMMARY_PDF (FileType) |
| storage_provider | `local` or `s3` |
| storage_path | e.g. `/app/storage/uploads/x.mp4` or `interview/<id>/summary.pdf` |
| file_size | BigInteger |

**otps** — legacy/fallback OTP table (email, otp_code, expires_at); the live flow uses Redis.

Migrations: `alembic upgrade head` (applied automatically in `start.sh` and the Docker file).

---

## API Reference

Base prefix: no global prefix — routes are mounted as `/auth` and `/interviews`. Interactive docs at `http://localhost:8000/docs` (OpenAPI).

### Auth (`/auth`)

| Method | Path | Auth | Description | Rate limit |
|---|---|---|---|---|
| POST | `/auth/register` | – | Create account, set access+refresh cookies | 5/min |
| POST | `/auth/login` | – | Login, set cookies | 5/min |
| POST | `/auth/logout` | – | Clear auth cookies | – |
| POST | `/auth/refreshToken` | refresh cookie | Mint a new access token | – |
| POST | `/auth/forgot-password` | – | Send OTP email | 5/min |
| POST | `/auth/resend-otp` | – | Resend OTP (30 s cooldown) | 3/min |
| POST | `/auth/verify-otp` | – | Verify OTP → verification_token cookie | 5/min |
| POST | `/auth/update-password` | verification cookie | Set new password | 5/min |

### Interviews (`/interviews`)

All interview routes require the `access_token` cookie (via `get_current_user`).

| Method | Path | Description | Rate limit |
|---|---|---|---|
| POST | `/interviews/upload` | Multipart `file` (+ optional `title`, `claimed_experience_years`); starts pipeline, returns `interview_id` | 10/hour |
| GET | `/interviews/{interview_id}/status` | Full processing status + scores (null until complete) | 120/min |
| POST | `/interviews/{interview_id}/cancel` | Cancel in-progress interview (not COMPLETED/FAILED/CANCELLED) | 10/min |
| GET | `/interviews/{interview_id}/report` | Streams the PDF (404 if not COMPLETED yet) | 30/min |
| GET | `/interviews/list` | Paginated list (`status`, `page`, `page_size`; CANCELLED excluded) | 60/min |
| GET | `/interviews/{interview_id}` | Detail incl. topic breakdown | 60/min |

Example upload flow:

```
1. POST /interviews/upload  (multipart video)
   → {"success": true, "message": "Interview uploaded successfully",
      "data": {"interview_id": "<uuid>", "status": "UPLOADED"}, "meta": null}

2. Poll GET /interviews/<uuid>/status until status == "COMPLETED" (or FAILED)

3. GET /interviews/<uuid>/report  → application/pdf download
```

---

## Response & Error Formats

Every endpoint returns a uniform envelope (`app/shared/response_handler/responseSchema.py`):

```json
{
  "success": true,
  "message": "Interview uploaded successfully",
  "data": { "interview_id": "...", "status": "UPLOADED" },
  "meta": null
}
```

- `data` holds the payload (note: IDs such as `interview_id` are **nested inside `data`**, not top-level).
- `meta` is used by list endpoints: `{total, page, page_size}`.

Errors use the same wrapper with `success: false` and a typed error:

```json
{
  "success": false,
  "message": "Interview not found",
  "error": { "error_code": "resource_not_found", "error_type": "..." }
}
```

Error codes include `authentication_error`, `acces_token_expired` (sic), `invalid_otp`, `otp_expired`, `invalid_verification_token`, `missing_verification_token`, `user_not_found`, `internal_server_error`, `resource_not_found`, `bad_request`, `entity_already_error`, `too_many_requests` (also raised by slowapi on rate-limit hits).

---

## Configuration (.env)

Everything is read from `.env` at import time by `app/core/config.py`; there is no default `.env.example` present, so copy the variables below. Required hard values: DB credentials, `SECRET_KEY`, `ALGORITHM`, cookie flags, token expiry, `BROKER_URL`, `GEMINI_API_KEYS`. Everything else has a default.

| Variable | Purpose |
|---|---|
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` | PostgreSQL connection (URL is built and password-encoded) |
| `SECRET_KEY`, `ALGORITHM` | JWT signing |
| `COOKIE_SECURE`, `COOKIE_HTTPONLY`, `COOKIE_SAMESITE` | Auth cookie flags |
| `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `VERIFICATION_TOKEN_EXPIRE_MINUTES` | Token lifetimes |
| `BROKER_URL` | Celery broker (e.g. `redis://localhost:6379/0`) |
| `CORS_ORIGINS` | JSON list of allowed origins |
| `REDIS_URL`, `REDIS_DATA_EXPIRE` | Redis endpoint + OTP/data TTL (seconds) |
| `FFMPEG_PATH`, `FFPROBE_PATH` | Default `ffmpeg` / `ffprobe` |
| `SILENCE_NOISE_THRESHOLD` (`-35dB`), `SILENCE_MIN_DURATION` (`10`) | Silence trimming |
| `GEMINI_API_KEYS` | Comma-separated keys — used for transcription, classifier, and (as primary provider) analysis |
| `GROQ_API_KEY` | Legacy (Whisper path was replaced by Gemini) — currently unused by the pipelines |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `FROM_EMAIL` | OTP email delivery |
| `QUESTION_BATCH_SIZE` (`15`) | Q&A batch size in the assessment node |
| `OPENAI_API_KEY` / `OPENAI_API_KEYS`, `ANTHROPIC_API_KEY` / `ANTHROPIC_API_KEYS` | Fallback providers (must also be added to `ACTIVE_PROVIDERS` in `retryManager.py`) |
| `OLLAMA_MODEL`, `OLLAMA_BASE_URL` | Local provider option |
| `LLM_CONCURRENCY_LIMIT`, `LLM_TIMEOUT_SECONDS` (`180`) | LLM safety knobs |
| `PRIMARY_PROVIDER` (`google`), `FALLBACK_PROVIDER` (`openai`), `ENABLE_PROVIDER_FALLBACK` | Provider selection |
| `INITIAL_RETRY_DELAY`, `BACKOFF_MULTIPLIER`, `MAX_RETRY_DELAY`, `MAX_RETRIES`, `ENABLE_RETRY_JITTER` | LLM retry policy |
| `MAX_CONCURRENT_INTERVIEWS` (`5`), `MAX_CONCURRENT_LLM_REQUESTS` (`10`), `QUEUE_WAIT_TIMEOUT` (`60`), `CONCURRENCY_BACKEND` (`local` / `redis`) | Pipeline gating |
| `ENABLE_CHECKPOINTING` (`true`) | LangGraph resume support |
| `ENABLE_PII_REDACTION` (`false`), `ENABLE_PROMPT_SANITIZATION`, `MAX_TRANSCRIPT_SIZE`, `MAX_TRANSCRIPT_DURATION`, `MAX_PROMPT_TOKENS`, `ON_LIMIT_EXCEEDED` | Input safety |
| `STORAGE_DIR` | Local PDF and media storage directory (default: `storage`) |
| `OLLAMA_MODEL`, `GOOGLE_AI_MODEL`, `OPENAI_MODEL`, `ANTHROPIC_MODEL` | Model names per provider |

---

## Setup & Running

### Prerequisites

- Python 3.11+
- PostgreSQL (or Docker)
- Redis (or Docker)
- ffmpeg + ffprobe on PATH (also used by pydub)
- `fpcalc` (Chromaprint) for duplicate detection
- Gemini API key(s)

### Option A — fully local

```bash
python -m venv venv && venv\Scripts\activate   # Windows; or `source venv/bin/activate` on Linux/macOS
pip install -r requirements.txt

# 1. write your .env (see Configuration)
# 2. start infra (or run postgres/redis natively)
docker compose up -d postgres redis

# 3. migrate + run API
alembic upgrade head
uvicorn app.main:app --reload

# 4. run the worker in another terminal
celery -A app.celery_app worker --loglevel=info --concurrency=2
```

### Option B — Docker Compose (full stack)

```bash
cp .env .env            # ensure DB_* and BROKER_URL match docker-compose
docker compose up --build
```

Compose starts: `postgres` (17, healthchecked), `redis` (7), `backend` (uvicorn on `:8000`), and `celery` (worker, concurrency 2, heartbeat/gossip/mingle disabled). Shared named volumes persist `storage/`, `uploads/`, and `logs/`.

Notes:

- The Celery **result backend is required to be PostgreSQL** — `celery_app.py` raises if `DATABASE_URL` is not `postgresql://`.
- `start.sh` (used by the Dockerfile) waits for Postgres, runs `alembic upgrade head`, then boots uvicorn.

---

## Testing

pytest with `tests/` mirroring the app layout:

- `tests/core/`, `tests/models/` — config, security, DB, ORM models
- `tests/managers/` — ffmpeg, transcription, langgraph managers
- `tests/graph/` — retry manager, provider strategy, validators, concurrency, security hardening
- `tests/services/`, `tests/tasks/`, `tests/shared/`, `tests/utils/` — services, Celery tasks, shared helpers, ffmpeg/transcription utilities
- `tests/api/` — HTTP-level tests for auth and interviews (uses `tests/.env.test`)

```bash
pytest                          # full suite
pytest tests/api -v             # API tests only
pytest --cov=app --cov-report=term-missing
```

---

## Quality Tooling

- **ruff** — lint + format (`pyproject.toml`: target py311, line-length 120; per-file ignores for tests/migrations).
- **mypy** — strict-ish typing check with pydantic + SQLAlchemy plugins.
- **pre-commit** — hooks configured in `.pre-commit-config.yaml`.
- **docker-compose.test.yml / Dockerfile.test** — test runs inside Docker.

```bash
ruff check .
ruff format --check .
mypy app
```

---

## Documentation

Developer documentation lives in the repo's `readme/` folder, but **`readme/` is git-ignored** (kept local-only), so the links below work on the current checkout only:

- [`readme/README.md`](readme/README.md) — **developer master README**: architecture, 4-step pipeline, LangGraph internals, scoring model, config deep-dive, operational gotchas.
- [`readme/module-kt/index.md`](readme/module-kt/index.md) — knowledge-transfer docs, one page per backend module (recommended reading order + pipeline/scoring quick reference).
- [`readme/testing.md`](readme/testing.md) — running tests (Docker + local), structure, markers.
- [`readme/workflow.md`](readme/workflow.md) — CI/CD pipeline walkthrough.
- [`readme/pre-commit.md`](readme/pre-commit.md) — pre-commit hooks setup and usage.