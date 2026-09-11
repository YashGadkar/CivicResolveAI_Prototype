# CivicResolve AI — Development & Operations

This repository contains a full-stack hackathon prototype for **PS02 — AI-Powered Citizen Complaint Understanding & Resolution Assistant**.

## Architecture

- `frontend/` — React + TypeScript + Vite + Tailwind CSS, shadcn-style primitives, Lucide, Recharts, Framer Motion.
- `backend/` — FastAPI + SQLAlchemy with a deterministic multilingual complaint-analysis pipeline.
- SQLite is the zero-config local/demo database. Set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL for deployment.
- Alembic owns reviewed database migrations for production/container deployments.
- No external AI API is required. The deterministic fallback performs classification, entity/duration extraction, priority selection, missing-information detection, department routing, recommendation generation and citizen-response generation.

## Run with Docker

```bash
docker compose up --build
```

Open `http://localhost:8080`.

The backend container applies `alembic upgrade head` before starting the API. The frontend reverse-proxies `/api/*` to FastAPI, so no API secret or backend hostname is exposed in browser code.

## Run locally

Backend:

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

For zero-config local development, `AUTO_CREATE_SCHEMA=true` remains available. Production containers set it to `false` and use Alembic migrations.

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## API

- `GET /health` — process liveness.
- `GET /ready` — database readiness.
- `POST /api/v1/complaints/analyze`
- `POST /api/v1/tickets` — supports `Idempotency-Key` to make submission retries safe.
- `GET /api/v1/tickets`
- `GET /api/v1/tickets/{ticket_code}`
- `PATCH /api/v1/tickets/{ticket_code}/status`
- `POST /api/v1/tickets/{ticket_code}/simulate-breach`
- `GET /api/v1/analytics`

FastAPI interactive docs are available at `/docs` when the backend is reachable directly.

Every HTTP response includes an `X-Request-ID`; request logs record request ID, method, path, status and duration without logging complaint bodies, contact fields or query strings. Ticket status changes are constrained by an explicit state machine, and a resolved ticket cannot silently return to an active state.

## Verification

CI verifies all of the following on every push to `main`:

```text
Backend dependency install
Alembic migration from an empty database
Python compile check
Pytest suite
Frontend dependency install
TypeScript typecheck
Production Vite build
```

The backend suite covers the acceptance scenarios plus API readiness/headers, duplicate detection, idempotent ticket creation, idempotency conflicts, status transition safety and SLA escalation.

## Honest prototype boundaries

The app deliberately labels prototype SLA rules and demo analytics. It does **not** claim official government integration, official SLA policy, real government dispatch, real government statistics, production deployment, or scientifically validated AI accuracy.

## Remaining hardening before a real civic deployment

A real municipality deployment should additionally add identity-provider backed citizen/officer/admin authentication, fine-grained role and tenant authorization, managed PostgreSQL, object storage plus malware scanning for attachments, queue-backed notifications, distributed rate limiting/WAF, centralized telemetry, secrets management, retention/privacy controls, backup/restore drills, accessibility testing, disaster recovery, and governed LLM evaluation if an external model is enabled.
