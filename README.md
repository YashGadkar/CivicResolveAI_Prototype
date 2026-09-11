# CivicResolve AI

> **From citizen complaint to accountable civic action.**

CivicResolve is a production-style national-hackathon prototype for multilingual citizen grievance intake, civic routing, employee operations, transparent ticket tracking and resolution feedback.

Citizens do not choose a preset scenario or civic category. They describe the real problem naturally. The platform can detect supported languages/scripts, separate multiple civic issues in one message, verify locations, route each issue, create independent trackable tickets and preserve an auditable service history.

## Current platform capabilities

### Citizen experience

- Secure citizen sign-up/sign-in with Gmail-format validation, strong password policy, Argon2 password hashing and HttpOnly JWT sessions
- Password show/hide and clean login form state after logout/reload
- Multilingual complaint intake without a language picker
- Multiple civic problems in one message can become separate tickets
- Verified location checks plus optional browser/device geolocation where supported
- Voice complaint input where the browser exposes speech recognition
- Supporting JPG, PNG, WebP, MP4 and PDF evidence
- Private **My Complaints** workspace and direct `CR-*` ticket tracking
- Related-report / duplicate incident awareness
- Configurable SLA progress and escalation visibility
- Citizen resolution confirmation, reopen/dispute flow and satisfaction feedback
- Safe ticket archive/withdraw behavior that preserves accountability history instead of destroying civic records
- Role-aware Civic Assistant with ticket-aware actions
- Installable PWA shell and mobile-first responsive UI
- Light/dark mode, larger-text accessibility control, keyboard focus styling and reduced-motion support

### Employee operations

- Separate employee login; public users cannot self-register as staff
- Staff-only complaint queue and citizen/ticket detail access
- Original citizen problem statement, contact context, evidence and audit trail in ticket detail
- Assignment, reassignment and department transfer workflows
- Resolution notes and resolution evidence
- Safety-risk flags, SLA escalation and incident visibility
- Related-report incident clustering
- Operational search/filtering across citizen, ticket, category, department and location
- Admin governance analytics with synthetic/demo labeling
- Civic Assistant for permitted ticket/queue/triage workflows

### Platform / production foundations

- FastAPI + SQLAlchemy backend with Alembic migrations
- SQLite for local prototype use; SQLAlchemy architecture prepared for PostgreSQL deployment
- Request IDs, security headers, readiness/liveness endpoints and audit events
- Idempotent ticket creation
- Role/ownership authorization boundaries
- Local evidence storage for the prototype with provider abstraction for production object storage
- Provider contracts for OTP, notifications/WhatsApp-style delivery and image-analysis integrations without falsely claiming those services are live
- Docker Compose and GitHub Actions CI

> External email/SMS OTP, WhatsApp Business, cloud object storage, malware scanning and managed image/speech services require approved provider credentials in a real deployment. The repository intentionally keeps safe local/disabled fallbacks so the prototype works without secrets.

## Stack

**Frontend:** React, TypeScript, Vite, Tailwind CSS, Lucide, Recharts, Framer Motion  
**Backend:** Python, FastAPI, SQLAlchemy, Pydantic, Alembic, Argon2, PyJWT  
**Database:** SQLite locally; PostgreSQL-ready SQLAlchemy configuration

## Project structure

```text
CivicResolveAi/
├── backend/
│   ├── app/
│   │   ├── core_routes.py
│   │   ├── platform_routes.py
│   │   ├── capability_routes.py
│   │   └── services/
│   ├── migrations/
│   └── tests/
├── frontend/
│   ├── public/
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

## Clone / update

```bash
git clone https://github.com/aniketchougule1902/CivicResolveAi.git
cd CivicResolveAi
```

For an existing Antigravity/Codebox clone:

```bash
git checkout main
git pull origin main
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
API:       http://localhost:8000
Swagger:   http://localhost:8000/docs
Health:    http://localhost:8000/health
Readiness: http://localhost:8000/ready
```

## Backend environment

Copy `backend/.env.example` to `backend/.env`. At minimum keep a long development JWT secret and the local database URL. Production deployments must use HTTPS-secure cookies, a unique secret, migrations and managed infrastructure.

Common settings include:

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
GEOCODER_BASE_URL=https://nominatim.openstreetmap.org
GEOCODER_COUNTRY_CODES=in
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

## Create an employee account

Public sign-up creates only citizen accounts. Provision staff from the backend environment:

```bash
cd backend
python -m app.scripts.create_staff \
  --name "Demo Officer" \
  --email officer@civicresolve.local \
  --role OFFICER
```

Use `ADMIN` for an administrator. Never hardcode production staff passwords in the repository.

## Frontend production verification

```bash
cd frontend
npm run typecheck
npm run build
```

## Backend verification

```bash
cd backend
python -m alembic upgrade head
python -m compileall app
python -m pytest -q
```

# Docker

The Docker stack requires a JWT secret:

```bash
export JWT_SECRET="replace-with-a-random-secret-longer-than-32-characters"
docker compose up --build
```

PowerShell:

```powershell
$env:JWT_SECRET="replace-with-a-random-secret-longer-than-32-characters"
docker compose up --build
```

Open `http://localhost:8080`.

# Important product boundaries

CivicResolve remains a hackathon prototype. It does **not** claim official government integration, official SLA policy, official statistics, emergency-dispatch capability, scientifically validated universal-language accuracy, live WhatsApp/SMS delivery or production-grade identity verification unless those services are separately configured and validated.

The deterministic multilingual pipeline intentionally fails safe to clarification or **Other Civic Service** when it cannot confidently identify a civic service. Emergency/safety signals are surfaced for human attention rather than represented as real emergency dispatch.
