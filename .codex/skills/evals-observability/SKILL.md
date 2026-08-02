---
name: evals-observability
description: Design or review ChronOS structured logs, request/workflow IDs, redaction, error classification, traces, deterministic evaluation cases, and provider/model metadata. Use for diagnostics, workflow quality, or share-readiness checks.
---

# Evals and Observability

## Required inputs

- User-visible behavior and failure modes
- Log/trace schema and sample events
- Evaluation cases, expected outcomes, and privacy constraints

## Workflow

1. Define observable success and classified failures.
2. Trace request ID, workflow ID, step, duration, validation, provider/model, outcome, and safe decision summary.
3. Redact secrets, tokens, authorization, raw provider payloads, and sensitive content.
4. Build deterministic fixtures for success, invalid output, unavailable provider, rate limit, timeout, and denied approval.
5. Compare actual output to explicit assertions; document uncertainty.

## Checks

- Operational code uses structured logging, not print.
- Public errors are stable and include request IDs where practical.
- Traces contain no hidden reasoning.
- Do not claim OpenTelemetry, Sentry, or Langfuse is active unless configured and tested.

## Commands

Run backend offline tests, search `rg -n "print\(|authorization|access_token|refresh_token" backend/app`, and inspect representative error responses.

## Expected output

Provide an evaluation matrix, failing cases, trace/log examples, redaction findings, and exact commands.

## Stop conditions

Stop before persisting secret/raw sensitive content or presenting an unevaluated metric as reliable.
