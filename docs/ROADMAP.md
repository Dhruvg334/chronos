# Roadmap

ChronOS has a complete planning and execution core: capture, daily and weekly planning, projects, outcomes, routines, focus, reflection, recovery, personalization, attributable memory, hybrid retrieval, read-first integrations, MCP foundations, operational controls, and deployment-ready boundaries.

The roadmap focuses on measured product improvement rather than expanding the core surface indiscriminately.

## Product validation

- Run browser-level journeys across onboarding, Inbox, Projects, Plan, Week, Focus, Recovery, Memory, Integrations, export, and deletion.
- Evaluate planning and recovery with larger human-reviewed scenarios and real user feedback.
- Measure retrieval precision using representative project notes and documents rather than synthetic fixtures alone.
- Refine empty, degraded, loading, and provider-failure states from observed use.

## Provider validation

- Validate production Google Calendar OAuth, refresh, synchronization, revocation, and cached fallback.
- Validate the semantic embedding provider under realistic documents and rate limits.
- Enable additional read-first connectors only after disposable-account OAuth and scope review.
- Keep external writes disabled until provider-specific approval, idempotency, audit, and rollback behavior is proven.

## Operational maturity

- Connect hosted error monitoring and OpenTelemetry-compatible traces through the existing redaction boundary.
- Establish practical SLOs for authenticated API availability, planning latency, provider degradation, and transaction success.
- Exercise backup restoration in an isolated hosted environment.
- Expand CI provider checks only where secrets can be protected from untrusted pull requests.
- Retire isolated compatibility tables and modules after retention and migration requirements are formally closed.

## Product extensions

Potential extensions are evaluated against user value, safety, and maintenance cost:

- desktop packaging;
- mobile companion experiences;
- shared workspaces and collaboration;
- notifications;
- controlled external write integrations;
- advanced analytics and longitudinal insights;
- paid capacity and organization controls.

These extensions must not weaken the current approval, provenance, ownership, and deterministic-feasibility boundaries.
