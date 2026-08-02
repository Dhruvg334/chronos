# Agent Runtime

ChronOS uses one bounded orchestration runtime.

Known-path workflows run deterministic steps. Agent steps may choose among typed tools or revise a proposal, but deterministic services retain ownership of time arithmetic, overlap checks, authorization, idempotency, and permissions.

`WorkflowRunner` enforces step and timeout limits and records observable trace events. `ToolSpec` defines typed input/result models, permission class, read/write status, timeout, idempotency, and audit category. `RecommendationFirstApprovalPolicy` allows reads, gates internal writes, and always requires approval for external writes.

Traces store workflow and step names, reason category, selected tool, validation result, duration, provider/model metadata, outcome, error classification, and concise decision summaries. They do not store hidden reasoning.

The intake flow is the first provider/repository-injected representative workflow. Scheduling and contextual recovery currently remain known-path deterministic flows.
