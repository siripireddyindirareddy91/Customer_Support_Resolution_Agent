# Delivery Support Resolution Agent

A delivery-support application built around a guarded LangGraph workflow. The initial local experience runs without external credentials: deterministic intent routing, customer-scoped demo order tools, policy evidence retrieval, resolution validation, and a FastAPI chat API. An OpenAI-compatible model can be enabled for low-confidence intent classification with environment configuration.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

Open `http://localhost:8000/docs`. In development, obtain a short-lived bearer token from `POST /api/v1/auth/demo` with `{"customer_id":"CUS-1001"}`, then call `POST /api/v1/chat` with that bearer token and a JSON body such as `{"message":"Where is order ORD-1001?"}`. Demo customers are `CUS-1001` and `CUS-1002`; orders are deliberately isolated by customer.

Run tests with `pytest`.

## Architecture

The API validates the request and authenticated customer context before invoking a compiled LangGraph workflow. The graph performs input guardrails, intent classification, supervision/planning, deterministic specialist routing, authorized tools, policy retrieval, grounded resolution, critic review, validation, and response generation. Invalid resolutions take a bounded replanning path; missing order context and human requests are handled explicitly. LangChain tools are deny-by-default and enforce customer ownership at the tool boundary.

The local customer/order adapter uses seeded in-memory examples. Request telemetry is persisted to `database/observability.db` in SQLite WAL mode. Each API request receives request, trace, session, conversation, and agent-run IDs; chat adds a LangGraph workflow span. Logs contain operational metadata and intent, not raw customer messages or credentials. Observability APIs are development-only and fail closed in other environments. Replace demo identity and customer/order adapters before production use. No refund/cancellation mutation is enabled in this demo. See [docs](docs/architecture/system-architecture.md) for boundaries and limitations.

## Local infrastructure

`docker compose up --build` starts the API, frontend, PostgreSQL with pgvector, and Redis. SQLite telemetry is stored on the API container filesystem in this local Compose setup; mount a persistent volume to retain it across container recreation. PostgreSQL/pgvector and Redis are included as target infrastructure but are not connected to the workflow yet. Copy `.env.example` to `.env` and configure secrets before exposing the service beyond a local machine.

## Vercel

Deploy the `frontend/` directory as a Next.js Vercel project and set `BACKEND_API_ORIGIN` to a public HTTPS FastAPI origin. See [Vercel deployment notes](docs/deployment/vercel.md). The frontend is configured but production deployment is not ready until a backend origin, production identity provider, and persistent telemetry storage are provisioned.