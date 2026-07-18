# Auburn Ridge Leasing Platform

Production-grade apartment leasing platform for **Auburn Ridge Townhomes**
(2610 Davison Ave, Auburn Hills, MI 48326 — theauburnridge.com).

Monorepo:

```
apps/web        Next.js 14 (App Router, TypeScript, Tailwind)  — public site, portal, admin
apps/api        FastAPI (Python 3.11, SQLAlchemy 2, Alembic)   — REST API + chatbot proxy
apps/worker     Celery worker + beat                           — analytics, news, alerts
packages/shared-types   Shared TypeScript API types
```

## Quick start (local dev)

```bash
cp .env.example .env      # fill in secrets — never commit .env
docker compose up --build
```

- Web: http://localhost:3000
- API: http://localhost:8000 (OpenAPI docs at /docs, health at /healthz)
- On first boot the API container runs Alembic migrations and seeds sample data
  (3 floor plans, 20 units, 24 months of price history, residents/leases,
  5 sample leads, 3 sample news items, pricing rules).

## Environment variables

| Variable | Used by | Purpose |
|---|---|---|
| `DATABASE_URL` | api, worker | Postgres DSN (`postgresql+psycopg://…`) |
| `REDIS_URL` | api, worker | Cache, Celery broker, rate limiting |
| `OLLAMA_API_KEY` | api | Ollama Cloud key for the chatbot (server-side only, never shipped to the browser) |
| `NEWS_API_KEY` | worker | NewsAPI.org key for the local-news cron |
| `SENDGRID_API_KEY` | worker | Alert emails |
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` / `TWILIO_FROM_NUMBER` | worker | Alert SMS |
| `SENTRY_DSN` | api, worker, web | Error monitoring (optional) |

All secrets live in `.env` / a secret manager only. `.env` is gitignored.

## Build phases

- [x] **Phase 1 — Scaffold + DB + seed**: monorepo, docker-compose, full schema (13 tables) with Alembic migration, idempotent seed with 24 months of synthetic price history, `/healthz`, `GET /api/floor-plans`, `GET /api/availability`, web placeholder.
- [x] **Phase 2 — Public site + estimate tool**: home (hero, amenity grid, proximity strip, testimonials), `/floor-plans` (live availability + asking rents), `/estimate` 4-step wizard (rules-driven itemized estimate, email-gated lead capture, amenity-savings sidebar), `/news` (ISR 3 h, grouped by category), `/contact` tour form; `POST /api/estimate`, `POST /api/leads` (email+phone dedupe), `GET /api/news`; Redis rate limiting (fail-open).
- [x] **Phase 3 — Chatbot ("Ridgeline Assistant")**: FastAPI proxy to Ollama Cloud (key server-side only, `OLLAMA_URL`/`OLLAMA_MODEL` configurable), SSE streaming `POST /api/chat` with per-request system prompt (property facts + live availability injected from DB, fair-housing guardrails), transcript persistence in `chat_sessions`, `POST /api/chat/extract` (defensive JSON parse → lead upsert, source=chatbot), graceful office-phone fallback when the LLM is unreachable, streaming widget on all public pages with "Saved — the office will follow up" confirmation. Set `OLLAMA_API_KEY` in `.env` for live replies.
- [ ] Phase 4 — Resident portal + auto-renewal + maintenance
- [ ] Phase 5 — Analytics worker + admin dashboard
- [ ] Phase 6 — News + alerts + CI/ops hardening

## Architecture

```
Next.js 14 (web) ──► FastAPI (api) ──► PostgreSQL 16
                        │   ▲              ▲
                        ▼   │              │
                      Redis 7 ◄── Celery worker + beat (analytics / news / alerts)
                        │
                        ▼
                 Ollama Cloud (chatbot, server-side key)
```

See `01-SYSTEM-DESIGN.md` (project brief) for the full design.
