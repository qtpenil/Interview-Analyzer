# InteReview — Landing Site (standalone)

A standalone Next.js frontend containing **only the InteReview landing page** — no dashboard, auth pages, API clients, or backend wiring. Built from scratch to mirror the landing experience of the main `InteReview-frontend` app.

## Stack

- Next.js 16 (App Router) + React 19 + TypeScript
- Tailwind CSS v4 (CSS-first tokens via `@theme inline`)
- `lucide-react` icons, Geist fonts

## What's inside

```
src/
├── app/
│   ├── page.tsx        # landing composition + SEO metadata
│   ├── layout.tsx      # fonts, theme cookie init, ambient background
│   └── globals.css     # theme tokens, utilities, keyframes
├── components/
│   ├── landing/        # Navbar, Hero, TrustBar, Problem, Features,
│   │                   # Workflow (+ DemoVideo), DashboardPreview, Reports,
│   │                   # WhyChooseUs, FAQ, CTA, Footer + primitives
│   │                   # (Button, ScrollLink, ScrollToTop, Reveal,
│   │                   # SectionHeading, MockPanels)
│   ├── common/ScoreRing.tsx
│   └── ThemeToggle.tsx
├── hooks/              # useSmoothScroll, useTheme
├── providers/ThemeProvider.tsx
└── styles/theme.ts     # dark / light token sets
public/videos/demo.mp4  # demo clip shown in the Workflow section
```

Sections on the page, in order: Navbar → Hero → TrustBar → Problem → Features → Workflow (demo video + 6 steps) → DashboardPreview → Reports → WhyChooseUs → FAQ → CTA → Footer. Light/dark theme toggle included (persisted via cookie + localStorage).

## Run it

```bash
npm install
npm run dev      # http://localhost:3000
npm run build    # production build
npm start        # serve the production build
```

## Notes / wiring

- Auth CTAs (`/login`, `/register`, `/dashboard`) are kept as relative links so they can be pointed at the main app later. This build has no auth session, so the logged-out variants always render.
- Replace `public/videos/demo.mp4` with your own clip if needed — the player shows a graceful error state when the file is missing.
