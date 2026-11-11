# ResolveFlow AI

ResolveFlow is a customer support workspace for investigating delivery exceptions. It uses synthetic order, tracking, carrier, support history, and policy data. The application persists investigations, review decisions, policies, audit events, and evaluation runs.

## Run locally

With Docker and Compose, run `docker compose up --build` and open `http://localhost:8000`. The stack includes PostgreSQL.

For development, install Python 3.12 and Node.js 22 or later. In one terminal run:

```sh
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

In another terminal run:

```sh
npm ci
npm run dev
```

Open `http://localhost:5173`. Vite proxies API calls to FastAPI. Local development defaults to SQLite for records and a separate SQLite file for LangGraph checkpoints. Set a persistent `JWT_SECRET` to preserve sessions across server restarts.

The service creates its initial schema on first boot. To apply the versioned application schema explicitly, run `alembic upgrade head` with the same database environment. The LangGraph checkpoint store manages its own schema.

## Try the workflow

Register an account and investigate `ORD-10452` with the complaint “My package is overdue and tracking has stopped updating.” The workflow looks up the order, classifies the issue, retrieves policy passages, and recommends a next step. Open Agent Workflow to inspect stage outputs and timestamps. Try `ORD-10453` for a failed attempt and `ORD-10454` for conflicting delivery evidence.

The review queue resumes the saved graph checkpoint after an authorized decision. An operator can assign a role from a trusted environment with database access:

```sh
python -m backend.manage reviewer@example.com SUPPORT_MANAGER
```

Register the reviewer first. Support agents can access their own investigations. Support managers and administrators can review pending investigations across accounts in the single-organization demo. Review decisions record an authorization outcome. The demo has no refund, payment, cancellation, or carrier write integrations.

## Architecture

- **Frontend** uses React, TypeScript, Vite, Lucide and Recharts. Charts are computed from stored investigations, and workflow progress polls stored execution traces.
- **Backend** uses FastAPI, Argon2 password hashes, signed JWTs and SQLAlchemy. Swagger UI is at `/api/docs`.
- **Workflow** uses a typed LangGraph state, four stages, bounded retries and an interrupt before consequential actions. SQLite and PostgreSQL checkpoint implementations support local and hosted execution.
- **Evidence** includes 42 synthetic orders and 126 tracking events, plus carrier updates, support history and eight sample policies. The relational migration adds foreign-key-backed domain tables for roles, customers, shipments, agent runs, classifications, resolutions, approvals, policy chunks, and evaluation results. Startup backfills these records from existing API snapshots without dropping historical data.
- **Policy search** ranks eligible passages with FAISS. It uses deterministic local vectors by default and supports hosted semantic embeddings for the synthetic catalog. PDF, DOCX and UTF-8 TXT are supported.
- **Evaluation** runs 15 normal, ambiguous and adversarial fixtures against the same graph and saves results. Reports show category pass rates, a classification confusion matrix and changes from the previous run. Evaluation and investigation records can be exported as CSV.

## Verification

Set `MODEL_API_BASE`, `MODEL_API_KEY`, and `DRAFT_MODEL` to enable customer-response generation through a provider compatible with `/chat/completions`. Vercel AI Gateway also supports production OIDC authentication. The provider receives the verified finding and recommended action. Raw complaints, identifiers, and uploaded policies are excluded. A template is used if generation is disabled or unavailable. Drafting leaves the approval rules intact.

To enable hosted semantic search for the synthetic policy catalog, set `EMBEDDING_MODEL` alongside the provider base URL and key. Search queries are sent to the configured provider when hosted semantic search is active. Uploaded policy documents use local FAISS vectors.

```sh
python -m pip install pytest httpx
python -m pytest -q
npm ci
npm run build
```

Set `RESOLVEFLOW_DATA_DIR` to a temporary directory with PostgreSQL environment variables unset to isolate SQLite integration tests. The tests create synthetic accounts, investigations, review decisions and an evaluation run.

## Deploy to Vercel

Create a Vercel project from this repository and connect a persistent PostgreSQL database. Configure `DATABASE_URL` (or `POSTGRES_URL_NON_POOLING`) and a stable random `JWT_SECRET` of at least 32 characters in the production environment. The database role needs schema creation permissions on first boot.

Deploy from the repository root with `vercel deploy --prod`. The static build is served from `dist` and the Python function serves FastAPI under `/api`. Verify `/api/health` and register a synthetic demo account before running an investigation.
