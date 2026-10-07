from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.observability.telemetry import list_rows, overview, require_development_observability, trace_detail

router = APIRouter(prefix="/api/observability", tags=["observability"], dependencies=[Depends(require_development_observability)])
api_router = APIRouter(prefix="/api", tags=["observability"], dependencies=[Depends(require_development_observability)])


def page(table: str, limit: int, offset: int, search: str | None) -> dict[str, Any]:
    return {"items": list_rows(table, limit, offset, search), "limit": limit, "offset": offset, "source": "sqlite"}


@router.get("/overview")
def get_overview() -> dict[str, Any]:
    return overview()


@router.get("/logs")
@api_router.get("/logs")
def get_logs(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), search: str | None = None) -> dict[str, Any]:
    return page("application_logs", limit, offset, search)


@router.get("/metrics/requests")
@api_router.get("/metrics/requests")
def get_request_metrics(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), search: str | None = None) -> dict[str, Any]:
    return page("requests", limit, offset, search)


@router.get("/traces")
@api_router.get("/traces")
def get_traces(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), search: str | None = None) -> dict[str, Any]:
    return page("traces", limit, offset, search)


@router.get("/traces/{trace_id}")
@api_router.get("/traces/{trace_id}")
def get_trace(trace_id: str) -> dict[str, Any]:
    result = trace_detail(trace_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return result


@api_router.get("/metrics/agents")
def get_agent_metrics() -> dict[str, Any]:
    data = overview()["agent_runs"]
    return {**data, "source": "sqlite"}