# InteReview Frontend

Web client for **InteReview** — an AI-powered candidate interview analysis platform. Users upload interviewer/candidate recordings (video or audio); the backend transcribes, runs AI analysis, and produces a scored interview report. The frontend handles authentication, upload + real-time processing tracking, the interview repository, and rich per-interview detail views.

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Getting Started](#getting-started)
3. [Scripts](#scripts)
4. [Environment Variables](#environment-variables)
5. [Project Structure](#project-structure)
6. [Architecture Overview](#architecture-overview)
7. [Routing & Pages](#routing--pages)
8. [Core Data Flows](#core-data-flows)
9. [Interview Detail — Data Contract](#interview-detail--data-contract)
10. [Theme System](#theme-system)
11. [Styling Conventions](#styling-conventions)
12. [Components & Hooks Reference](#components--hooks-reference)
13. [Persistence Keys](#persistence-keys)
14. [Backend Contract](#backend-contract)
15. [Quality & Testing](#quality--testing)
16. [Common Tasks / Extending](#common-tasks--extending)
17. [Gotchas & Checklist](#gotchas--checklist)

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Framework | **Next.js 16** (App Router, `app/` directory, client + server components) |
| Language | **TypeScript** (strict) |
| Rendering | React 19 (client components throughout the app surface) |
| Styling | **Tailwind CSS v4** (`@theme inline` tokens) + CSS custom properties |
| UI Primitives | `@base-ui/react` (headless), `lucide-react` icons, `@radix-ui/react-switch` |
| State | React Context: `AuthContext`, `UploadContext`, `ThemeProvider` |
| HTTP | Axios (single `apiClient`, response interceptor), `js-cookie` |
| Fonts | `next/font/google` (Geist Sans + Geist Mono) |
| Build tooling | Next.js 16 dev server (Turbopack by default), `tsc`, ESLint 9 |

---

## Getting Started

```bash
# install dependencies
npm install

# run the app against a local backend (see env vars below)
npm run dev

# production build + start
npm run build
npm run start
```

Open `http://localhost:3000`. The backend (FastAPI) is expected at `http://localhost:8000`.

> **Important:** auth is cookie-based (see [Auth Model](#auth-model)). CORS/credentials must be enabled on the backend, otherwise cookies will not be sent and every protected call will 401.

---

## Scripts

| Command | What it does |
|---------|--------------|
| `npm run dev` | Next.js dev server (Turbopack) |
| `npm run build` | Production build |
| `npm run start` | Serve the production build |
| `npm run lint` | ESLint (`eslint`) across the repo |
| `npx tsc --noEmit` | Type check (strict) |

There is **no unit-test suite yet** — see [Quality & Testing](#quality--testing).

---

## Environment Variables

Create `.env.local` at the repo root:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000   # backend base URL (no trailing slash)
```

Note: the variable is `NEXT_PUBLIC_API_BASE_URL` (see `src/services/apiClient.ts`). If unset, it falls back to `http://localhost:8000`.

---

## Project Structure

```
src/
├── app/                         # Next.js App Router
│   ├── layout.tsx               # Root layout: Theme > Auth > Upload providers, Sidebar, ambient bg
│   ├── page.tsx                 # Landing page (marketing)
│   ├── globals.css              # Tailwind v4 @theme inline, token fallbacks, keyframes
│   ├── dashboard/               # Upload + live processing workspace (protected)
│   │   └── page.tsx
│   ├── interviews/              # Repository list (protected)
│   │   ├── page.tsx             #   list: search / decision filter / sort
│   │   └── [id]/page.tsx        #   detail: flip-cards, concepts, questions, PDF download
│   ├── login/                   # Sign in
│   ├── register/                # Sign up (auto-logs-in after success)
│   └── forgot-password/         # Forgot → verify-otp → update-password (3 pages)
│       ├── page.tsx
│       ├── verify-otp/page.tsx
│       └── update-password/page.tsx
├── components/
│   ├── ui/                      # Progress (headless bar), FilterSelect (headless select)
│   ├── upload/                  # FileUpload, SelectedFileCard, InterviewDetailsCard,
│   │                            #   AnalyzeInterviewButton, ProcessingTracker, CompletionBanner
│   ├── auth/                    # AuthShell, AuthCard (shared auth page chrome)
│   ├── common/                  # Sidebar (desktop nav + mobile drawer)
│   ├── landing/                 # Hero, Features, FAQ, CTA, Footer, Navbar, etc.
│   └── ThemeToggle.tsx          # Dark/light switch
├── services/
│   ├── apiClient.ts             # Axios instance, interceptor, envelope unwrap, error extractor
│   ├── authApi.ts               # login/register/logout/forgot/verify/update
│   └── interviewApi.ts          # upload, status, list, detail, cancel, report download
├── context/
│   ├── AuthContext.tsx          # Session state, JWT/cookie handling, login/register/logout
│   └── UploadContext.tsx        # Upload → processing state machine + resume-on-refresh
├── providers/
│   └── ThemeProvider.tsx        # Token → CSS var mapping, persistence, SSR hydration
├── hooks/
│   ├── useRequireAuth.ts        # Route guard (verify session, 1 retry, fallback redirect)
│   ├── useTheme.ts              # Theme context consumer
│   ├── useSmoothProgress.ts     # Easing of raw byte upload progress
│   ├── useSmoothScroll.ts       # Smooth scroll helper
│   ├── useStageProgress.ts      # Anti-stall analysis progress model
│   └── useTypedStatus.ts        # Typewriter status message rotation
├── styles/
│   └── theme.ts                 # darkTheme / lightTheme design tokens
├── types/                       # api.ts, auth.ts, interview.ts
├── lib/                         # cn(), validators, passwordReset helpers
└── constants/ , utils/          # (reserved dirs, currently unused)
```

---

## Architecture Overview

### Providers chain (`app/layout.tsx`)

```
ThemeProvider(initialTheme)
  └─ AuthProvider
       └─ UploadProvider
            └─ Sidebar + <children>  (scroll container + ambient animated background)
```

- `ThemeProvider` maps design tokens → CSS custom properties on `<html>`.
- `AuthProvider` owns the session; `UploadProvider` owns upload/processing state and only functions when authenticated.
- `layout.tsx` is a **server component** (`cookies()` reads the theme cookie) — it suppresses hydration warnings and injects `themeInitScript` in `<head>` to apply the theme before paint (no flash).

### Auth model (critical)

The backend authenticates **purely via httpOnly cookies** (`access_token`, `refresh_token`) — it never inspects an `Authorization` header, and the frontend **cannot read or set those cookies via JS**. Therefore:

- `apiClient` is created with `withCredentials: true` so the browser attaches cookies automatically. **There is no request interceptor adding a token.**
- The only interceptor work is on responses:
  - **401** → call `refreshClient.post('/auth/refreshToken')` (a separate Axios instance to avoid interceptor recursion). The backend sets a fresh access-token cookie from the refresh cookie. Concurrent 401s queue behind a single refresh (`failedQueue`); the original request is retried with the new cookie.
  - **Refresh fails** → clear `session_hint`, hard-navigate to `/login` via `window.location.href`.
- `session_hint` (localStorage) is a **non-privileged** UI hint containing the user's `{name, email}`. It is used only to avoid a flash of the login page on refresh. Real authorization is enforced by the backend through the cookies.
- Auth endpoints are **unwrapped** responses (see envelope below) — `login()`/`register()` receive the `User` object directly.

### Response envelope unwrapping (`apiClient.ts`)

Every backend success response is:

```json
{ "success": true, "message": "...", "data": <T>, "meta": { total, page, page_size } | null }
```

The response interceptor unwraps it: callers receive `response.data` = the payload's `data` field, and `response.meta` = the envelope's `meta`. Blob responses (`responseType: 'blob'`) and message-only responses (`data: null`) are skipped. Errors are normalized by `extractApiError()` (handles `{message}`, `{detail}` string, and FastAPI 422 `detail` arrays).

---

## Routing & Pages

| Route | Access | Purpose |
|-------|--------|---------|
| `/` | public | Marketing landing page |
| `/login` | public | Sign in |
| `/register` | public | Sign up (auto sign-in) |
| `/forgot-password` | public | Request password reset (OTP sent to email) |
| `/forgot-password/verify-otp` | public | Verify OTP (`?email=` query param) |
| `/forgot-password/update-password` | public | Set new password |
| `/dashboard` | protected | Upload + live processing tracker |
| `/interviews` | protected | Repository list (search/filter/sort) |
| `/interviews/[id]` | protected | Full report detail |

**Protection:** pages call `useRequireAuth()` and render a "Verifying your session…" spinner while `status === "checking"`. `AuthProvider` additionally verifies the session on mount for protected `pathname`s and hard-redirects on failure.

---

## Core Data Flows

### 1. Authentication

`login(credentials)` → `authApi.login` → envelope unwrapped to `User` → save `session_hint` → `setIsAuthenticated(true)` → `router.push('/dashboard')`.

`register(credentials)` → `authApi.register` → **auto-login** with the same credentials.

`logout()` → `authApi.logout` (`POST /auth/logout`) → clear local state. (Backend route must clear the httpOnly cookies server-side; the TODO is noted in `authApi.ts`.) Local state is cleared even if the request fails.

On mount, `AuthProvider`:
1. Optimistically restores `session_hint` (if parseable).
2. Verifies the **real** session with `getInterviews(100)` — but **only on protected routes** (calling it on `/login` would 401 and trip the interceptor's hard redirect → infinite reload loop).
3. On failure: clears the hint, and if on a protected route, pushes to `/login`.

### 2. Upload → Processing → Report (`UploadContext`)

Phase machine (`UploadPhase`), derived from state atoms (never drifted by a parallel setState):

```
idle → uploading → uploaded → processing → completed
                        └──────────────→ failed
```

- `handleAnalyze()` guards against re-entry when `uploadProgress !== null`, then calls `uploadInterview(file, experience, abortSignal, onProgress)` — a raw byte-progress provided directly by Axios.
- Progress is **monotonic-clamped** in `uploadInterview` (never decreases; prevents chunked-encoding/retry glitches).
- After the upload returns `interview_id`, `pollInterviewStatus(id)` polls `GET /interviews/{id}/status` every **4s**. Backend statuses map to the stage UI: `UPLOADED → PROCESSING → TRANSCRIBING → ANALYZING → COMPLETED`.
- Up to **4 consecutive poll failures** are tolerated before declaring a network error.
- Failure-ish statuses (`/fail|error|invalid|not_an_/i`) are treated as terminal even if they aren't the literal `FAILED` string.
- The derived `phase` drives which UI (upload card, tracker, completion banner) `dashboard/page.tsx` shows.

**Refresh resilience:** the active `interview_id` is persisted to localStorage (`intereview-active-interview`) and upload progress to sessionStorage (`intereview-upload-progress`). On re-mount (after auth resolves), `UploadContext` restores the stored interview and either shows `COMPLETED`/`FAILED`/`CANCELLED` or resumes polling.
**User switch:** when `user.email` changes, all upload state resets.

### 3. Interviews list (`/interviews`)

- `getInterviews()` fetches `GET /interviews/list?page_size=100` → `{ items, meta }`.
- Load happens only after `useRequireAuth()` reports `authed`.
- **Search / filter / sort are all client-side** against the fetched array:
  - search: title substring (case-insensitive).
  - decision filter: `ALL | NONE | STRONG_HIRE | HIRE | BORDERLINE | NO_HIRE` (via `FilterSelect`).
  - sort: `NEWEST | OLDEST | SCORE` (score uses `overall_score` with `""`-as-0 handling).
  - `FAILED` and `CANCELLED` interviews are always hidden.

### 4. Interview detail (`/interviews/[id]`)

- Fetches `GET /interviews/{id}`; score fields are normalized to strings (Decimal→string on the wire).
- **Topics & Concepts Coverage** card uses a CSS 3D flip scene (`flip-scene` / `flip-inner` / `flip-face`) — front face shows a topic grid, back face shows the selected topic's concept score, confidence, and Strong/Weak concept pills. `flipToTopic(topic)` / `flipToList()` toggle the `is-flipped` class with a mirrored animation.
- **Question-by-Question Evaluation** timeline: renders the per-topic embedded `questions` aggregated into a flat `detail.questions` array (category = topic name, score = `average_score`).
- **Sidebar metrics** (`ScoreRing`, sliders) show overall / technical / communication / confidence / knowledge-depth / experience-alignment scores.
- **Download Report** → `GET /interviews/{id}/report` (blob), saved as `interview-report-…pdf`.

---

## Interview Detail — Data Contract

The backend detail payload embeds rich per-topic data. `interviewApi.ts` maps it into the UI types (`src/types/interview.ts`):

- **Concepts are objects, not strings.** Each `strongest_concepts`/`weakest_concepts` entry is `{ concept: string, question_ids: string[] }` (question_ids link to the interview question UUIDs the concept came from). `mapConcepts()` normalizes legacy string entries into this object shape defensively.
- **Questions are per-topic.** `topics[].questions[]` items have the shape `{ id, question_number, question, answer, average_score, difficulty, strong_concepts, weak_concepts, feedback }`. The detail page aggregates them into `detail.questions` with `category` set to the topic name (`mapEmbeddedQuestion`).
- **All `Decimal` scores arrive as strings** (e.g. `"8.0"`). The mapping layer converts nullable numbers/strings to `"0"` defaults where a number is expected.

```ts
export interface ConceptRef {
  concept: string;
  question_ids: string[];
}

export interface InterviewTopic {
  topic: string;
  average_score: string;
  confidence_score: string;
  strongest_concepts: ConceptRef[];
  weakest_concepts: ConceptRef[];
  feedback?: string;
  questions?: InterviewQuestion[];
}

export interface InterviewQuestion {
  id: string;
  question: string;
  answer: string;
  score: string;     // average_score normalized
  feedback: string;
  category: string;  // topic name for embedded questions
  question_number?: number;
  difficulty?: string | null;
  strong_concepts?: string[];
  weak_concepts?: string[];
}
```

---

## Theme System

**Architecture:** `src/styles/theme.ts` defines `darkTheme` / `lightTheme` token objects. `ThemeProvider` writes them as CSS custom properties on `<html>`; Tailwind `@theme inline` in `globals.css` maps them to utilities (`bg-background`, `text-primary`, `border-default`, `shadow-shadow`, `ring-ring`, …).

**Tokens (dark — monochrome):** `background #000`, `surface #0A0A0A`, `card #111`, `elevated #181818`, `accent #555`, silver `btnPrimaryFrom/To` gradient, white-halo shadows, etc.

**Persistence:** cookie `intereview-theme` (SSR-readable) + localStorage fallback. The root layout reads the cookie server-side and renders `theme-dark` / `theme-light` + `data-theme` on `<html>`; `themeInitScript` in `<head>` sets the class before hydration — no flash, no hydration mismatch. `ThemeToggle` animates via CSS vars.

**Rules:**
- No hardcoded hex/rgba in components. Exceptions: arbitrary utility values that *point at* token vars (`shadow-[var(--shadow)]`, `from-[var(--btn-primary-from)]`) and the translucent `tracker-sheen` gradient (reads the same in both themes).
- New tokens must be added to **both** themes, the `cssVarMap`, **and** `globals.css` `@theme inline`.

---

## Styling Conventions

- Tailwind v4 with `@theme inline`; all colors/shadows/rings flow from tokens.
- Arbitrary values only for one-off geometry or token-var references.
- Animations/keyframes live in `globals.css` (e.g. `tracker-sheen`, `tracker-pulse-ring`, `tracker-breathe`, `tracker-caret`, `tracker-message-in`, `auth-float`, `auth-grid-pan`, `flip-*`). Decorative looping trackers are disabled under `@media (prefers-reduced-motion: reduce)`.
- Dark-mode shadows use white-halo (`shadow-[var(--shadow)]`).

---

## Components & Hooks Reference

| Component | Purpose |
|-----------|---------|
| `Progress` | Headless progress bar (`@base-ui`) with optional shimmer sheen; `aria-label`, `aria-busy` |
| `FilterSelect` | Headless dropdown selection used for decision filter |
| `ProcessingTracker` | Animated stage timeline + anti-stall bar + typed status rotation |
| `StageTimeline` / `StageIndicator` | 5-stage stepper (horizontal desktop / vertical mobile) inside tracker |
| `FileUpload` | Drag-and-drop zone with validation + preview |
| `SelectedFileCard` | Selected file summary chip |
| `InterviewDetailsCard` | Interview title + experience inputs |
| `AnalyzeInterviewButton` | Primary CTA: upload / processing / completed states |
| `CompletionBanner` | Success state with download + "Analyze Another" |
| `Sidebar` | Persistent nav (desktop) + mobile drawer |
| `ThemeToggle` | Animated dark/light switch |
| `AuthShell` / `AuthCard` | Shared chrome for login/register/forgot pages |
| `ScoreRing` | Circular score indicator (detail page) |

| Hook | Purpose |
|------|---------|
| `useRequireAuth` | Verifies session; 1 retry (1.5s) before fallback redirect to guard transient blips |
| `useTheme` | Reads `ThemeContext` |
| `useSmoothProgress` | Eases raw byte progress into a smooth climb |
| `useStageProgress` | Anti-stall per-stage target + eased display value (analysis phase only) |
| `useTypedStatus` | Typewriter effect (32ms/char) + 2s hold + fade/slide rotation |
| `useSmoothScroll` | Smooth scroll helper |

### Processing tracker internals (non-obvious)

- **Anti-stall model (`useStageProgress`):** per-stage safe ranges `Uploading 0→20, Preparing 20→40, Transcribing 40→60, Processing with AI 60→90, Completed 100`. A *target* recomputed every 200ms approaches the stage cap exponentially (`1 - 0.5^(elapsed/halfTime)`, half-times `[4s, 8s, 16s, 90s, 0]`), and a *display* value eases toward it every 50ms with capped steps — smooth motion, never crossing the cap, no fake 100%. On `isCompleted` it drives cleanly to exactly 100. **Upload phase does NOT use this hook** — it uses real byte progress via `useSmoothProgress`.
- **Status messages** live in `STATUS_DETAILS` in `ProcessingTracker.tsx` (single source of truth), keyed by backend status. Stage changes produce a new array → `useTypedStatus` resets instantly.
- All transition timers run in async callbacks (never synchronously in an effect body) and are cleaned up on re-run/unmount.
- On error: shimmer/typed-status/cancel hidden, a `role="alert"` box replaces the footer, progress halts.

---

## Persistence Keys

| Key | Storage | Kind | Purpose |
|-----|---------|------|---------|
| `session_hint` | localStorage | non-privileged | `{name,email}` UI hint to avoid login flash |
| `intereview-active-interview` | localStorage | `{interviewId, savedAt}` | Resume polling after refresh/reopen |
| `intereview-upload-progress` | sessionStorage | `{progress}` | Keep upload bar state across reload |
| `intereview-theme` | cookie + localStorage | `dark`/`light` | Theme persistence (SSR-readable) |

---

## Backend Contract

```
POST   /auth/login                    → { success, message, data: User }
POST   /auth/register                 → { success, message, data: User }
POST   /auth/logout                   → clears httpOnly cookies  (TODO'd in authApi)
POST   /auth/refreshToken             → sets new access_token cookie
POST   /auth/forgot-password          → sends OTP
POST   /auth/verify-otp               → verifies OTP
POST   /auth/update-password          → sets new password
POST   /interviews/upload             → multipart file → { interview_id, status: "UPLOADED" }
GET    /interviews/{id}/status        → { status, failure_reason?, reason? }
POST   /interviews/{id}/cancel        → cancel in-flight interview
GET    /interviews/list?page_size=N   → { items, meta }
GET    /interviews/{id}               → detail (topics + embedded questions + concepts + scores)
GET    /interviews/{id}/report        → PDF blob (skips envelope unwrap)
```

Status values: `UPLOADED | PROCESSING | TRANSCRIBING | ANALYZING | COMPLETED | FAILED | CANCELLED`. Auth is cookie-based for every route except the public auth pages.

---

## Quality & Testing

- **TypeScript strict** — always verify with `npx tsc --noEmit`.
- **ESLint 9** (`eslint.config.mjs`, React Compiler-era rules like `react-hooks/set-state-in-effect`). Some **pre-existing** warnings/errors exist in legacy files (e.g. `useSmoothProgress.ts`); when linting, scope to the files you touched.
- **No automated unit tests yet** — add Vitest + React Testing Library if the team grows the suite.

---

## Common Tasks / Extending

| Task | Where to look |
|------|---------------|
| Add a new processing status | `STAGES` + `getStageIndex` + a `STATUS_DETAILS` entry in `ProcessingTracker.tsx` |
| Retime typed rotation | args to `useTypedStatus` (defaults 32ms/char, 2000ms hold) |
| Retune anti-stall speed | `STAGE_RANGES` / `STAGE_HALF_TIME_SEC` in `useStageProgress.ts` |
| Change upload smoothing | `useSmoothProgress` call in `ProcessingTracker.tsx` |
| Add a theme token | `ThemeTokens` + both themes in `styles/theme.ts` + `cssVarMap` + `@theme inline` in `globals.css` |
| Change interview detail mapping | `mapConcepts` / `mapEmbeddedQuestion` in `services/interviewApi.ts` |
| New landing section | component in `components/landing/` → import in `app/page.tsx` |
| New protected page | wrap with `useRequireAuth()` and render a spinner while `"checking"` |
| New endpoint | add to `services/*Api.ts` → consume in context/component |
| New tracker animation | keyframe + class in `globals.css`, gated under `prefers-reduced-motion` |

---

## Gotchas & Checklist

- [ ] New status added to **both** `getStageIndex`/`STAGES` **and** `STATUS_DETAILS`?
- [ ] New stage added to `STAGE_RANGES` / `STAGE_HALF_TIME_SEC`?
- [ ] Theme token added to both themes + `cssVarMap` + `globals.css`?
- [ ] New API error path handled in the `pollInterviewStatus` switch?
- [ ] Persistence keys unique if adding more (see [Persistence Keys](#persistence-keys))?
- [ ] Never send/read `access_token`/`refresh_token` as headers or JS cookies — auth cookies are httpOnly and managed by the browser + backend.
- [ ] Don't call protected endpoints on public routes (interceptor will hard-redirect to `/login`).
- [ ] Blob downloads must not be unwrapped by the envelope interceptor (`responseType: 'blob'`).
- [ ] Keep score fields as strings when they come from `Decimal` — `parseFloat`/`.toFixed` in the UI, never display raw.
- [ ] Cancel button wired to aborting the Axios signal (`AbortController`) + `resetUploadState`.
- [ ] Clear `intereview-active-interview` on `resetUploadState`.

---

*Keep this file updated as the codebase evolves.*