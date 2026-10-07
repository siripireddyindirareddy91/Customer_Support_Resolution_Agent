import json
import sqlite3
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from backend.app.config.settings import settings


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid4())


request_context: ContextVar[dict[str, str]] = ContextVar("request_context", default={})


def require_development_observability() -> None:
    if settings.app_env != "development":
        raise HTTPException(status_code=404, detail="Not found")


def connect() -> sqlite3.Connection:
    path = Path(settings.observability_db_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[3] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=5000")
    return connection


def initialize() -> None:
    with connect() as database:
        database.executescript("""
            CREATE TABLE IF NOT EXISTS requests (
                request_id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                agent_run_id TEXT NOT NULL,
                method TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                duration_ms REAL NOT NULL,
                environment TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at);
            CREATE INDEX IF NOT EXISTS idx_requests_trace_id ON requests(trace_id);
            CREATE TABLE IF NOT EXISTS application_logs (
                id INTEGER PRIMARY KEY,
                request_id TEXT NOT NULL,
                trace_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                agent_run_id TEXT NOT NULL,
                level TEXT NOT NULL,
                service TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT NOT NULL,
                metadata TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON application_logs(timestamp);
            CREATE INDEX IF NOT EXISTS idx_logs_trace_id ON application_logs(trace_id);
            CREATE TABLE IF NOT EXISTS traces (
                trace_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                agent_run_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                duration_ms REAL NOT NULL,
                started_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_traces_started_at ON traces(started_at);
            CREATE TABLE IF NOT EXISTS spans (
                span_id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL,
                parent_span_id TEXT,
                name TEXT NOT NULL,
                span_type TEXT NOT NULL,
                status TEXT NOT NULL,
                duration_ms REAL NOT NULL,
                metadata TEXT NOT NULL,
                started_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON spans(trace_id);
        """)


def record_log(message: str, level: str = "INFO", status: str = "ok", metadata: dict[str, Any] | None = None) -> None:
    context = request_context.get()
    if not context:
        return
    with connect() as database:
        database.execute(
            "INSERT INTO application_logs (request_id,trace_id,session_id,conversation_id,agent_run_id,level,service,endpoint,message,status,metadata,timestamp) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (context["request_id"], context["trace_id"], context["session_id"], context["conversation_id"], context["agent_run_id"], level, "support-api", context.get("endpoint", ""), message, status, json.dumps(metadata or {}, separators=(",", ":")), now()),
        )


def record_agent_run(intent: str, workflow_status: str, duration_ms: float, node_count: int) -> None:
    context = request_context.get()
    if not context:
        return
    timestamp = now()
    with connect() as database:
        database.execute(
            "INSERT INTO spans (span_id,trace_id,parent_span_id,name,span_type,status,duration_ms,metadata,started_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (new_id(), context["trace_id"], context.get("api_span_id"), "langgraph_workflow", "agent", workflow_status.lower(), duration_ms, json.dumps({"intent": intent, "node_count": node_count}), timestamp),
        )
        database.execute(
            "INSERT INTO application_logs (request_id,trace_id,session_id,conversation_id,agent_run_id,level,service,endpoint,message,status,metadata,timestamp) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (context["request_id"], context["trace_id"], context["session_id"], context["conversation_id"], context["agent_run_id"], "INFO", "langgraph", context.get("endpoint", ""), "workflow_completed", workflow_status.lower(), json.dumps({"intent": intent, "duration_ms": duration_ms, "node_count": node_count}), now()),
        )


def record_request(context: dict[str, str], method: str, endpoint: str, status_code: int, duration_ms: float) -> None:
    started_at = context["started_at"]
    status = "ok" if status_code < 500 else "error"
    with connect() as database:
        database.execute(
            "INSERT INTO requests VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (context["request_id"], context["trace_id"], context["session_id"], context["conversation_id"], context["agent_run_id"], method, endpoint, status_code, duration_ms, settings.app_env, now()),
        )
        database.execute(
            "INSERT INTO traces VALUES (?,?,?,?,?,?,?,?,?)",
            (context["trace_id"], context["request_id"], context["session_id"], context["conversation_id"], context["agent_run_id"], f"{method} {endpoint}", status, duration_ms, started_at),
        )
        database.execute(
            "INSERT INTO spans VALUES (?,?,?,?,?,?,?,?,?)",
            (context["api_span_id"], context["trace_id"], None, "api_request", "http", status, duration_ms, json.dumps({"method": method, "endpoint": endpoint, "status_code": status_code}), started_at),
        )
        database.execute(
            "INSERT INTO application_logs (request_id,trace_id,session_id,conversation_id,agent_run_id,level,service,endpoint,message,status,metadata,timestamp) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (context["request_id"], context["trace_id"], context["session_id"], context["conversation_id"], context["agent_run_id"], "INFO" if status == "ok" else "ERROR", "support-api", endpoint, "request_completed", status, json.dumps({"method": method, "status_code": status_code, "duration_ms": duration_ms}), now()),
        )


def list_rows(table: str, limit: int = 50, offset: int = 0, search: str | None = None) -> list[dict[str, Any]]:
    allowed = {"application_logs", "traces", "requests", "spans"}
    if table not in allowed:
        raise ValueError("Unsupported telemetry table")
    with connect() as database:
        if search:
            column = "trace_id" if table in {"traces", "spans"} else "message" if table == "application_logs" else "endpoint"
            rows = database.execute(f"SELECT * FROM {table} WHERE {column} LIKE ? ORDER BY rowid DESC LIMIT ? OFFSET ?", (f"%{search}%", limit, offset)).fetchall()
        else:
            order_by = "started_at" if table in {"traces", "spans"} else "timestamp" if table == "application_logs" else "created_at"
            rows = database.execute(f"SELECT * FROM {table} ORDER BY {order_by} DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
    return [dict(row) for row in rows]


def trace_detail(trace_id: str) -> dict[str, Any] | None:
    with connect() as database:
        trace = database.execute("SELECT * FROM traces WHERE trace_id=?", (trace_id,)).fetchone()
        if trace is None:
            return None
        spans = database.execute("SELECT * FROM spans WHERE trace_id=? ORDER BY started_at", (trace_id,)).fetchall()
        logs = database.execute("SELECT * FROM application_logs WHERE trace_id=? ORDER BY timestamp", (trace_id,)).fetchall()
    return {"trace": dict(trace), "spans": [dict(row) for row in spans], "logs": [dict(row) for row in logs]}


def overview() -> dict[str, Any]:
    with connect() as database:
        requests = database.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN status_code < 500 THEN 1 ELSE 0 END) AS successful, AVG(duration_ms) AS avg_ms, MAX(duration_ms) AS max_ms FROM requests").fetchone()
        errors = database.execute("SELECT COUNT(*) FROM requests WHERE status_code >= 500").fetchone()[0]
        traces = database.execute("SELECT COUNT(*) FROM traces").fetchone()[0]
        logs = database.execute("SELECT COUNT(*) FROM application_logs").fetchone()[0]
        agent_runs = database.execute("SELECT COUNT(*) FROM spans WHERE span_type='agent'").fetchone()[0]
        agent_failures = database.execute("SELECT COUNT(*) FROM spans WHERE span_type='agent' AND status IN ('invalid','error','failed')").fetchone()[0]
    total = requests["total"] or 0
    return {
        "requests": {"total": total, "successful": requests["successful"] or 0, "failed": errors, "success_rate": round((total - errors) / total, 4) if total else None, "average_latency_ms": round(requests["avg_ms"], 2) if requests["avg_ms"] is not None else None, "max_latency_ms": round(requests["max_ms"], 2) if requests["max_ms"] is not None else None},
        "traces": traces,
        "logs": logs,
        "agent_runs": {"total": agent_runs, "failed": agent_failures},
        "source": "sqlite",
    }