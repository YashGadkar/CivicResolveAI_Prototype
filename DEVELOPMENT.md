# CivicResolve AI — Development & Operations

This repository contains a full-stack hackathon prototype for **PS02 — AI-Powered Citizen Complaint Understanding & Resolution Assistant**.

## Architecture

- `frontend/` — React + TypeScript + Vite + Tailwind CSS, shadcn-style primitives, Lucide, Recharts, Framer Motion.
- `backend/` — FastAPI + SQLAlchemy with a deterministic multilingual complaint-analysis pipeline.
- SQLite is the zero-config local/demo database. Set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL for deployment.
- No external AI API is required. The deterministic fallback performs classification, entity/duration extraction, priority selection, missing-information detection, department routing, recommendation generation and citizen-response generation.

## Run with Docker

```bash
docker compose up --build
```

Open `http://localhost:8080`.

The frontend reverse-proxies `/api/*` to the FastAPI service, so no browser-side API secret or backend hostname is exposed.

## Run locally

Backend:

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## API

- `GET /health`
- `POST /api/v1/complaints/analyze`
- `POST /api/v1/tickets`
- `GET /api/v1/tickets`
- `GET /api/v1/tickets/{ticket_code}`
- `PATCH /api/v1/tickets/{ticket_code}/status`
- `POST /api/v1/tickets/{ticket_code}/simulate-breach`
- `GET /api/v1/analytics`

FastAPI interactive docs are available at `/docs` when the backend is reachable directly.

## Honest prototype boundaries

The app deliberately labels prototype SLA rules and demo analytics. It does **not** claim official government integration, official SLA policy, real government dispatch, real government statistics, production deployment, or scientifically validated AI accuracy.

## Production hardening path

The current prototype already separates API, persistence, analysis services and UI. Before a real civic deployment, add authenticated citizen/officer/admin identities, role/tenant authorization, PostgreSQL migrations (Alembic), object storage and malware scanning for attachments, queue-backed notifications, rate limiting/WAF, structured telemetry, secrets management, data retention/privacy controls, backups/restore drills, accessibility testing, and a governed LLM adapter if external AI is enabled.
