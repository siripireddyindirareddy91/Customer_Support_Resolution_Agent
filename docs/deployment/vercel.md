# Vercel deployment

## Frontend

Create a Vercel project from this repository and set **Root Directory** to `frontend`. Vercel detects Next.js. Use `npm install` as the install command and `npm run build` as the build command. Add the environment variable `BACKEND_API_ORIGIN` for Production, Preview, and Development, pointing to the public HTTPS origin of the separately deployed FastAPI service (for example, `https://support-api.example.com`, with no trailing slash). The frontend proxies `/api/*` requests to that origin with a Next.js rewrite.

The Vercel build intentionally fails when `BACKEND_API_ORIGIN` is missing or is not HTTPS. This prevents a deployed site from silently sending browser requests to `localhost` or using an insecure API origin.

## Backend and data

Vercel hosts the Next.js frontend in this setup. Deploy FastAPI as a container on a service that supports long-running Python applications, then configure `BACKEND_API_ORIGIN`. Do not deploy the current SQLite telemetry file as Vercel function storage: function filesystems are ephemeral and concurrent writes are not a durable shared database. The current API only exposes observability endpoints in development, and the customer demo-login endpoint is development-only; production identity and persistent telemetry/database adapters are prerequisites for a production-connected deployment.

## Local verification

The local Next.js config defaults `BACKEND_API_ORIGIN` to `http://localhost:8000` outside Vercel. Run the frontend from `frontend/` and FastAPI on port 8000. The same-origin `/api` rewrite should serve chat and telemetry without browser CORS configuration.