# Agent Runtime

ChronOS uses one bounded orchestration runtime for model and tool workflows. Known-path planning remains deterministic.

`WorkflowRunner` enforces maximum steps, a combined model/tool request budget, and per-step timeout. It preserves request, workflow, run, and idempotency identifiers. Success, timeout, step limit, request budget, schema validation, denied approval, tool failure, and unexpected failure receive concise classified trace events.

`ToolRegistry` rejects unknown names. `ToolSpec` validates arguments and returned values with Pydantic schemas and declares permission, timeout, idempotency, and audit category. Model tool selection is passed through registry validation and `RecommendationFirstApprovalPolicy` before execution. Reads need no approval, internal writes require explicit approval unless an idempotent internal automation was deliberately enabled, and external writes always require explicit approval.

`WorkflowTraceRepository` creates, completes, and fails runs and appends concise events. Events contain operational facts and safe summaries, not raw prompts, provider payloads, secrets, or hidden reasoning.

Intake is the representative end-to-end workflow: the injected repository creates the run, structured extraction consumes one request unit, the runtime persists its trace, and only user-approved drafts are persisted.

Adaptive planning and recovery may receive an expiring context pack. The pack is a bounded, cited compilation of structured state, confirmed memory, and retrieved excerpts. Retrieved text is explicitly labeled untrusted in provider requests, cannot select permissions or authorize tools, and is omitted without blocking the workflow when retrieval fails. Deterministic feasibility and recommendation-first approval remain authoritative.
