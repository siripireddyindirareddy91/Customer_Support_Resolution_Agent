import time
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.chat import router as chat_router
from backend.app.api.routes.customers import router as customers_router
from backend.app.api.routes.knowledge_base import router as knowledge_base_router
from backend.app.api.routes.observability import api_router as observability_api_router
from backend.app.api.routes.observability import router as observability_router
from backend.app.observability.telemetry import initialize, new_id, record_request, request_context
from backend.app.config.settings import settings

app = FastAPI(title="Customer Support Resolution Agent", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(customers_router)
app.include_router(observability_router)
app.include_router(observability_api_router)
app.include_router(knowledge_base_router)

initialize()


@app.middleware("http")
async def instrument_request(request, call_next):
    started = time.perf_counter()
    context = {
        "request_id": new_id(),
        "trace_id": new_id(),
        "session_id": new_id(),
        "conversation_id": new_id(),
        "agent_run_id": new_id(),
        "api_span_id": new_id(),
        "endpoint": request.url.path,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    token = request_context.set(context)
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        for key in ("request_id", "trace_id", "session_id", "conversation_id", "agent_run_id"):
            response.headers[f"X-{key.replace('_', '-').title()}"] = context[key]
        return response
    finally:
        duration_ms = (time.perf_counter() - started) * 1000
        try:
            record_request(context, request.method, request.url.path, status_code, duration_ms)
        except Exception:
            if settings.app_env == "development":
                raise
        request_context.reset(token)


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "delivery-support-resolution-agent"}