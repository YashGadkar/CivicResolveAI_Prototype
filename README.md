# CivicResolve AI

> **From Citizen Complaint to Government Action — Automatically.**

CivicResolve AI is a production-style hackathon prototype for **PS02 — AI-Powered Citizen Complaint Understanding & Resolution Assistant**.

It converts an unstructured civic complaint into a structured, prioritized, routed and trackable government-service ticket using a real deterministic multi-stage processing pipeline. The application works without an external AI provider and supports English, Hindi and Marathi demo flows.

## Features

- Natural-language citizen complaint submission
- English, Hindi and Marathi complaint handling
- Civic category classification across multiple public-service domains
- Entity, locality, landmark and duration extraction
- LOW / MEDIUM / HIGH / CRITICAL priority assessment
- Missing-information detection and clarification questions
- Automatic department routing
- Dynamic `CR-*` ticket generation
- Configurable prototype SLA deadlines and SLA state tracking
- SLA breach simulation and automatic escalation
- Resolution recommendations for officers
- Citizen-facing generated responses
- Duplicate complaint detection
- Immutable-style audit timeline for important ticket actions
- Citizen complaint tracking
- Department Officer Dashboard
- Admin analytics dashboard using clearly labelled synthetic/demo data
- AI Command Center showing the multi-agent processing workflow
- Request IDs, readiness checks and privacy-safe request logging
- Idempotent ticket creation for safe client retries
- Explicit ticket status transition rules
- Alembic database migrations
- Docker support
- GitHub Actions CI for backend tests, migrations, type checking and production builds

## Tech Stack

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn-style UI primitives
- Lucide icons
- Recharts
- Framer Motion

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Alembic
- SQLite for local/demo use
- PostgreSQL-compatible SQLAlchemy configuration for deployment

## Project Structure

```text
CivicResolveAi/
├── backend/              # FastAPI application, services, migrations and tests
├── frontend/             # React + TypeScript application
├── .github/workflows/    # CI workflow
├── docker-compose.yml    # Full-stack Docker setup
├── DEVELOPMENT.md        # Development and operations notes
└── README.md
```

# Quick Start — Run Frontend and Backend Locally

You need two terminals: one for the backend and one for the frontend.

## Prerequisites

Install:

- **Python 3.11+**
- **Node.js 22+**
- **npm**
- **Git**

Docker is optional if you prefer the container setup described later.

## 1. Clone the repository

```bash
git clone https://github.com/aniketchougule1902/CivicResolveAi.git
cd CivicResolveAi
```

# Backend Setup

Open a terminal in the repository root.

## Windows PowerShell / CMD

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## macOS / Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URLs:

```text
API:          http://localhost:8000
Swagger Docs: http://localhost:8000/docs
Health:       http://localhost:8000/health
Readiness:    http://localhost:8000/ready
```

# Backend Environment Setup

For local development, copy:

```text
backend/.env.example
```

to:

```text
backend/.env
```

Default local configuration:

```env
ENVIRONMENT=development
DATABASE_URL=sqlite:///./civicresolve.db
CORS_ORIGINS=http://localhost:5173,http://localhost:8080
ALLOWED_HOSTS=*
AUTO_CREATE_SCHEMA=true
```

### Environment variables

| Variable | Purpose | Local default |
| --- | --- | --- |
| `ENVIRONMENT` | Runtime environment name | `development` |
| `DATABASE_URL` | SQLAlchemy database connection URL | `sqlite:///./civicresolve.db` |
| `CORS_ORIGINS` | Comma-separated browser origins allowed by the API | `http://localhost:5173,http://localhost:8080` |
| `ALLOWED_HOSTS` | Comma-separated accepted host names | `*` |
| `AUTO_CREATE_SCHEMA` | Allows zero-config schema creation during development | `true` |

No external AI API key is required for the working prototype. Complaint analysis uses the built-in deterministic fallback pipeline.

For a production-style environment, prefer:

```env
ENVIRONMENT=production
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE_NAME
CORS_ORIGINS=https://your-frontend.example.com
ALLOWED_HOSTS=api.your-domain.example.com
AUTO_CREATE_SCHEMA=false
```

When `AUTO_CREATE_SCHEMA=false`, apply migrations before starting the API:

```bash
python -m alembic upgrade head
```

> Do not commit real database passwords, API keys or other secrets to Git.

# Frontend Setup

Open a **second terminal** from the repository root.

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

The frontend does **not require an environment file for local development**. Vite proxies frontend requests automatically:

```text
/api/*  -> http://localhost:8000
/health -> http://localhost:8000
```

Therefore, keep the backend running on port `8000` while using the frontend development server.

## Frontend production build

```bash
cd frontend
npm install
npm run typecheck
npm run build
```

The production output is generated in:

```text
frontend/dist/
```

# Copy-Paste Codebox Commands

If your IDE or cloud Codebox provides separate terminal tabs, use the following.

## Terminal 1 — Backend

### Windows

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

### macOS / Linux / most cloud Codeboxes

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Terminal 2 — Frontend

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

For a local machine, browse to:

```text
http://localhost:5173
```

For a browser-based Codebox, expose/open port `5173` for the frontend and port `8000` if you want to access FastAPI/Swagger directly.

# Run Everything with Docker

If Docker and Docker Compose are installed, this is the easiest full-stack startup method:

```bash
docker compose up --build
```

Then open:

```text
http://localhost:8080
```

The backend container runs the Alembic migrations before starting FastAPI. The production frontend container reverse-proxies API requests to the backend service.

Stop the stack with:

```bash
docker compose down
```

To rebuild after dependency or Dockerfile changes:

```bash
docker compose down
docker compose up --build
```

# Run Backend Tests

```bash
cd backend
python -m pytest -q
```

The suite covers the core acceptance flows including water supply, potholes, garbage collection, streetlights, Marathi complaints, ticket creation, duplicate detection, safe idempotent retries, API readiness, ticket status transitions and SLA escalation.

# Useful API Endpoints

```text
GET    /health
GET    /ready
POST   /api/v1/complaints/analyze
POST   /api/v1/tickets
GET    /api/v1/tickets
GET    /api/v1/tickets/{ticket_code}
PATCH  /api/v1/tickets/{ticket_code}/status
POST   /api/v1/tickets/{ticket_code}/simulate-breach
GET    /api/v1/analytics
```

`POST /api/v1/tickets` supports the `Idempotency-Key` header so a client can safely retry ticket creation without unintentionally creating duplicate tickets.

# Demo Flow

A primary demo complaint is:

```text
There has been no water supply in our area for three days and nobody is responding.
```

Expected analysis:

```text
Category: Water Supply
Duration: 3 days
Priority: HIGH
Department: Water Supply Department
Location: Missing
```

The system asks for missing location information. Enter for example:

```text
Shivaji Nagar
```

The application can then create a dynamic ticket such as:

```text
CR-XXXX
```

The ticket includes its category, priority, department, location, status, SLA, recommendation, citizen response and audit timeline.

# CI Verification

Every push to `main` runs checks for:

```text
Backend dependency installation
Fresh-database Alembic migration
Python compile check
Backend pytest suite
Frontend dependency installation
TypeScript typecheck
Production Vite build
```

# Prototype Boundaries

CivicResolve AI is currently a **hackathon prototype**. It intentionally does not claim:

- official government database access
- official government dispatch
- official SLA policy
- real government complaint statistics
- scientifically validated AI accuracy
- production deployment by a municipality

Prototype SLA values and analytics are labelled accordingly in the application.

For more technical and operational details, see [`DEVELOPMENT.md`](DEVELOPMENT.md).
