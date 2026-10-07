# API specification

Base URL: `http://localhost:8000`. Interactive schema: `/docs`.

## `GET /health`

Returns service health without customer data.

## `POST /api/v1/auth/demo`

Development only. Body: `{"customer_id":"CUS-1001"}`. Returns a one-hour bearer token. Returns 404 outside development.

## `POST /api/v1/chat`

Requires `Authorization: Bearer <token>`. Body: `{"message":"Where is order ORD-1001?","session_id":"optional","order_id":"optional"}`. The response includes `response`, `intent`, `workflow_status`, optional verified `order` and `delivery`, `resolution`, source `citations`, `escalation`, and safe `activity` messages.

The frontend uses `CUS-1001` for local demonstration. This identity flow is not an end-user login implementation.

## Development observability APIs

Each request adds `X-Request-Id`, `X-Trace-Id`, `X-Session-Id`, `X-Conversation-Id`, and `X-Agent-Run-Id` response headers. Chat responses include the same identifiers in their JSON body.

- `GET /api/observability/overview` returns SQL-aggregated request totals, success rate, latency, traces, logs, and workflow-run counts.
- `GET /api/logs?limit=50&offset=0&search=...` returns paginated structured event records.
- `GET /api/metrics/requests?limit=50&offset=0&search=...` returns measured request records.
- `GET /api/traces?limit=50&offset=0&search=...` returns trace summaries.
- `GET /api/traces/{trace_id}` returns correlated spans and logs.
- `GET /api/metrics/agents` returns observed workflow span counts.
- `GET /api/customers` returns the demo customer/order counts.
- `GET /api/knowledge-base` returns local Markdown policy document metadata.

Telemetry is written to SQLite at `OBSERVABILITY_DB_PATH` (default `database/observability.db`) with WAL, foreign keys, and a busy timeout. Observability endpoints return 404 unless `APP_ENV=development`; production observer-role authentication and the remaining LLM/RAG/system metric families are not implemented in this increment.