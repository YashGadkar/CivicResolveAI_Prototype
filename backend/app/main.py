import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .capability_routes import router as capability_router
from .config import get_settings
from .core_routes import router as core_router
from .database import Base, engine, get_db
from .intelligence_routes import router as intelligence_router
from .platform_routes import router as platform_router

settings = get_settings()
logger = logging.getLogger("civicresolve.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate_security()
    if settings.auto_create_schema:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.6.0",
    description="Multilingual civic complaint understanding, routing and resolution platform.",
    lifespan=lifespan,
)

if settings.allowed_host_list != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_host_list)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Idempotency-Key", "X-Request-ID"],
)

app.include_router(core_router)
app.include_router(intelligence_router)
app.include_router(platform_router)
app.include_router(capability_router)


@app.middleware("http")
async def request_context(request: Request, call_next):
    supplied_request_id = request.headers.get("X-Request-ID", "").strip()
    request_id = supplied_request_id[:128] if supplied_request_id else str(uuid.uuid4())
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
        if request.url.path.startswith(f"{settings.api_prefix}/auth"):
            response.headers["Cache-Control"] = "no-store"
        return response
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info(
            "request_complete request_id=%s method=%s path=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            status_code,
            duration_ms,
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


@app.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("database_readiness_failed")
        raise HTTPException(status_code=503, detail="Database is not ready.") from exc
    return {"status": "ready", "database": "reachable"}
