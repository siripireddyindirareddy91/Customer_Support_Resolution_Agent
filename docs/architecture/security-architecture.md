# Security architecture

Chat requests require an expiring HS256 bearer token with issuer and audience validation. The demo-token endpoint is available only when `APP_ENV=development`; it accepts only the two seeded customer IDs. Production startup rejects the default or short signing secret. Set a unique secret through a managed secret provider and replace demo identity issuance with the organization's identity provider before deployment.

Order tools enforce customer ownership even after authentication. The API does not expose internal prompts or reasoning. Refund/cancel/replace tools are not enabled. This slice does not yet provide rate limiting, RBAC, PII redaction, audit persistence, CSRF/session cookies, or authorization for admin roles; do not expose it publicly as-is.