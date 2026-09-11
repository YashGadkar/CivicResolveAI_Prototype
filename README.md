# CivicResolve AI

> **From Citizen Complaint to Government Action — Automatically.**

CivicResolve AI is a production-style hackathon prototype for **PS02 — AI-Powered Citizen Complaint Understanding & Resolution Assistant**.

The citizen does **not** choose a prebuilt complaint scenario or civic category. They write the real problem naturally, and the backend pipeline automatically detects the complaint language, classifies the civic issue, extracts useful details, calculates urgency, detects missing information, routes the case to a department and creates a trackable ticket.

## Current features

- Secure citizen sign-in and sign-up
- Gmail-format account validation (`@gmail.com`)
- Strong password policy
- Argon2 password hashing
- HttpOnly JWT session cookie
- Public signup always creates a `CITIZEN` role; users cannot self-assign staff privileges
- Citizen ticket ownership and **My Complaints** workspace
- Automatic language detection — no citizen language picker
- Broad Unicode/script detection including Latin, Devanagari, Bengali, Gujarati, Gurmukhi, Tamil, Telugu, Kannada, Malayalam, Odia, Arabic, Cyrillic, Han, Japanese Kana, Hangul, Thai, Greek and Hebrew scripts
- Multilingual civic concept classification with deterministic fallback
- Category, duration, location, priority and department analysis
- Missing-information clarification questions
- Dynamic `CR-*` ticket creation
- Duplicate complaint detection
- Configurable prototype SLAs and escalation
- Citizen tracking and audit history
- Staff-only officer queue
- Admin-only analytics
- AI Command Center that accepts a real complaint instead of a preset demo scenario
- Alembic migrations, Docker support and GitHub Actions CI

> The prototype accepts Unicode complaints without requiring a language selection. The deterministic offline classifier has richer civic vocabulary for supported languages and safely falls back to **Other Civic Service** plus clarification when it cannot confidently determine the service. It does not claim perfect universal-language AI accuracy.

## Stack

**Frontend:** React, TypeScript, Vite, Tailwind CSS, Lucide, Recharts, Framer Motion  
**Backend:** Python, FastAPI, SQLAlchemy, Pydantic, Alembic, Argon2, PyJWT  
**Database:** SQLite locally; SQLAlchemy is structured for PostgreSQL deployment

## Project structure

```text
CivicResolveAi/
├── backend/
│   ├── app/
│   │   ├── services/auth.py
│   │   ├── services/pipeline.py
│   │   └── services/ticketing.py
│   ├── migrations/
│   └── tests/
├── frontend/
│   └── src/
├── docker-compose.yml
├── DEVELOPMENT.md
└── README.md
```

# Run locally

Use two terminals: one for FastAPI and one for Vite.

## Requirements

- Python 3.11+
- Node.js 22+
- npm
- Git

## Clone

```bash
git clone https://github.com/aniketchougule1902/CivicResolveAi.git
cd CivicResolveAi
```

## Backend

### Windows PowerShell / CMD

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### macOS / Linux / Codebox

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
Swagger:      http://localhost:8000/docs
Health:       http://localhost:8000/health
Readiness:    http://localhost:8000/ready
```

## Backend environment

Copy `backend/.env.example` to `backend/.env`.

```env
ENVIRONMENT=development
DATABASE_URL=sqlite:///./civicresolve.db
CORS_ORIGINS=http://localhost:5173,http://localhost:8080
ALLOWED_HOSTS=*
AUTO_CREATE_SCHEMA=true
JWT_SECRET=replace-this-with-a-long-random-secret-at-least-32-chars
JWT_EXP_HOURS=8
AUTH_COOKIE_NAME=civicresolve_session
AUTH_COOKIE_SECURE=false
```

Important settings:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy database connection |
| `JWT_SECRET` | Signs authenticated sessions; use a long random secret |
| `JWT_EXP_HOURS` | Session expiration |
| `AUTH_COOKIE_SECURE` | Set `true` when the real deployment is served over HTTPS |
| `CORS_ORIGINS` | Allowed frontend origins |
| `ALLOWED_HOSTS` | Allowed HTTP host names |
| `AUTO_CREATE_SCHEMA` | Local convenience only; deployments should use Alembic |

For an HTTPS production deployment:

```env
ENVIRONMENT=production
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
CORS_ORIGINS=https://your-domain.example
ALLOWED_HOSTS=your-domain.example
AUTO_CREATE_SCHEMA=false
JWT_SECRET=GENERATE_A_LONG_RANDOM_SECRET
AUTH_COOKIE_SECURE=true
```

Do not commit production secrets.

## Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

No frontend `.env` is required for local development. Vite proxies `/api/*` to `http://localhost:8000`.

## Frontend production verification

```bash
cd frontend
npm run typecheck
npm run build
```

# Docker

The Docker stack intentionally requires you to supply a JWT secret.

### macOS / Linux

```bash
export JWT_SECRET="replace-with-a-random-secret-longer-than-32-characters"
docker compose up --build
```

### PowerShell

```powershell
$env:JWT_SECRET="replace-with-a-random-secret-longer-than-32-characters"
docker compose up --build
```

Open `http://localhost:8080`.

The backend container runs `alembic upgrade head` before serving requests.

# Authentication behavior

Citizen accounts require a Gmail-format address ending in `@gmail.com` and a password with at least 10 characters, uppercase, lowercase, a number and a special character. Passwords are stored as Argon2 hashes. The browser session is carried by an HttpOnly cookie rather than frontend local storage.

Gmail ownership itself is **not** verified in this hackathon prototype. A real production deployment should add OTP/email-link verification.

### Roles

- `CITIZEN` — can submit, analyze, track and list their own complaints
- `OFFICER` — can access the department queue and update ticket state
- `ADMIN` — can access staff operations and analytics

Public sign-up cannot choose a staff role. Staff accounts should be provisioned by an administrator or identity provider in a real deployment.

# AI analysis flow

```text
Citizen complaint in natural language
        ↓
Language Detection Agent
        ↓
Complaint Understanding Agent
        ↓
Entity & Location Agent
        ↓
Priority & Urgency Agent
        ↓
Missing Information Agent
        ↓
Department Routing Agent
        ↓
Ticket Agent
        ↓
Resolution Recommendation Agent
        ↓
Citizen Response Agent
        ↓
SLA Monitoring / Escalation
```

The UI intentionally does **not** provide preset citizen complaint scenarios. The Command Center also accepts a complaint typed by the user so judges can inspect the real pipeline output.

# Tests

```bash
cd backend
python -m pytest -q
```

Current backend coverage includes authentication, Gmail/password validation, session protection, citizen/staff authorization boundaries, English acceptance cases, automatic Marathi detection, multilingual classification, clarification, duplicate detection, idempotency, ticket lifecycle and SLA escalation.

# Prototype boundaries

CivicResolve AI is still a hackathon prototype. It does not claim official government integration, official SLA policies, real government dispatch, real government statistics, verified Gmail ownership or scientifically validated universal-language accuracy.
