# Non-functional requirements

- **Security:** signed identity, ownership checks at tool boundaries, no mutation tools by default, secrets from environment.
- **Grounding:** operational facts come from tool results; policy guidance requires local source evidence.
- **Recoverability:** workflow state is structured, but durable checkpoints are not configured in this increment.
- **Availability and scale:** not measured. Demo data and policy reads are local and synchronous.
- **Observability:** safe activity labels are returned, but structured logs, tracing, and metrics are not configured.
- **Accessibility and responsiveness:** keyboard-submittable chat and responsive customer dashboard; verify with assistive technology before release.