# GridMind

A spreadsheet that researches for you. Rows are things (companies, people, products); columns are plain-English questions. Hit **Run** and an AI agent per cell searches the web, answers, and cites its source. The grid fills live, and every cell keeps a step-by-step trace.

**Stack:** FastAPI · LangGraph · Groq (gpt-oss) · Tavily/DuckDuckGo search · Supabase Postgres · Svelte 5 + Vite · Render (API) · Vercel (UI)

## Architecture

```
Browser ──REST──▶ FastAPI (stateless) ──▶ Supabase Postgres  (cells table = job queue)
   ▲                  │                          ▲
   │ SSE              │ enqueue                  │ claim (SKIP LOCKED) + results
   └──── EventBus ◀───┴──── Worker(s) ───────────┘
        (memory | Redis)       │
                               └─▶ LangGraph cell agent ─▶ Tavily / DDG ─▶ Groq
```

Cell agent: `plan_query → search → (read page if snippets are thin) → answer → (refine & loop, max 2×)`.

## System-design decisions

| Question | Decision |
|---|---|
| Where does the queue live? | In Postgres (`cells.status = queued`). No extra infra, survives restarts, inspectable. |
| Many instances picking the same job? | `claim_cells()` RPC uses `FOR UPDATE SKIP LOCKED`; claims are exclusive. |
| Instance dies mid-cell? | Claims carry `locked_at`; stale locks (>180s) are reclaimed → at-least-once. Graceful shutdown requeues in-flight cells. |
| Poison / flaky cells? | Bounded attempts with exponential backoff (future `queued_at`), then `error` state; one bad cell never blocks others. |
| Free-tier rate limits (Groq ~30 RPM, Tavily credits)? | Per-instance sliding-window limiters, retry with jitter on 429/5xx (honours `Retry-After`), TTL cache + in-flight de-dup of identical searches/page reads, DDG fallback when Tavily is exhausted. |
| Live updates across instances? | Events go through an `EventBus`: in-memory by default, Redis pub/sub when `REDIS_URL` is set. Events are best-effort; the DB is the source of truth and the client refetches a snapshot on SSE `ready`. |
| DB write amplification? | Status writes only on transitions; the trace is saved in one bulk insert at the end. Step events stream live without touching the DB. |
| Stale results after edits? | Editing a row/column deletes its cells; a result for a deleted/edited cell is discarded. |
| Abuse / cost control? | Row/column caps, input length limits, per-IP run & create limits, SSRF guard on page fetches (public IPs only, including redirects), prompt-injection-aware system prompt. |
| Split API from workers? | `RUN_WORKER=false` makes an API-only instance; all state is external, so scale each side independently. |
| Auth? | v1: unguessable UUID per sheet (capability URL). Adding Supabase Auth later = `owner_id` + RLS. |

Known limits: per-IP and LLM/search rate limits are per instance (use Redis counters to make them global); Render's free tier sleeps when idle (the first request wakes it, and the stale-lock reclaim covers interrupted work).

## Frontend

Svelte 5 + Vite SPA (`frontend/`), no UI framework: plain CSS on design tokens (see [frontend/DESIGN.md](frontend/DESIGN.md)). The landing page loads about 50 kB of gzipped JS and CSS (fonts excluded), and every page is code-split.

- **Pages:** landing (a live, self-filling demo sheet), sheets dashboard, new-sheet form with templates, sheet editor, pricing (with a usage estimator), use cases, docs.
- **Editor:** sticky headers and entity column; inline edit of rows and questions; paste a list to add rows; run all, run a row or column, or re-run a cell; live SSE fill; a trace drawer with sources and agent steps; CSV export; keyboard navigation (arrows, Enter, R, Esc). On phones it becomes a bottom sheet.
- **Demo mode:** with no `VITE_API_URL`, or while the API is unreachable, sheets live in `localStorage` and a simulated worker pool runs scripted agent traces against a small offline dataset, on the same `Backend` interface as the live client. Demo sheet ids start with `demo_`, so links always open against the right store.
- **Cold starts:** the app pings `/healthz`, shows a "waking server" state for Render's free tier, and offers demo mode in the meantime.
- **Themes:** separate light and dark palettes, following the system until toggled; `prefers-reduced-motion` stops parallax and auto-play.

## Run locally

```bash
cd backend
cp .env.example .env        # add GROQ_API_KEY (+ TAVILY_API_KEY, SUPABASE_* for real persistence)
uv sync
uv run uvicorn app.main:app --reload
uv run pytest
```

```bash
cd frontend
cp .env.example .env.local   # VITE_API_URL=http://localhost:8000 (leave empty for demo mode)
npm install
npm run dev                  # http://localhost:5173
npm run check && npm run build
```

Without `SUPABASE_*` it falls back to an in-memory store. For Supabase, run `backend/supabase/schema.sql` in the SQL editor first.

## API

`POST /api/sheets` · `GET /api/sheets/{id}` · `POST /api/sheets/{id}/columns|rows|run` · `PATCH|DELETE /api/columns|rows/{id}` · `GET /api/sheets/{id}/events` (SSE) · `GET /api/cells/{id}/steps` · `GET /healthz`

## Deploy

- **API:** Render Blueprint (`render.yaml`); set env vars from `backend/.env.example`.
- **UI:** Vercel, with root directory `frontend` (framework preset Vite; `vercel.json` adds the SPA rewrite and asset caching). Set `VITE_API_URL` to the Render URL and add the Vercel URL to the API's `FRONTEND_ORIGIN`.
