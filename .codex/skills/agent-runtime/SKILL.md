---
name: agent-runtime
description: Design, implement, or review ChronOS bounded workflows, typed tool selection, approval policy, trace semantics, provider gateway use, budgets, retries, and deterministic validation. Use for orchestration or agent-step work.
---

# Agent Runtime

## Required inputs

- Workflow goal and known deterministic steps
- Allowed tools and permission classes
- Step/time/request budgets
- Approval and trace requirements

## Workflow

1. Separate known-path workflow steps from genuine tool choice.
2. Keep time arithmetic, permissions, overlap checks, and authorization deterministic.
3. Define each tool with typed input/result, permission, timeout, idempotency, and audit category.
4. Apply recommendation-first approval before execution.
5. Validate model output before persistence or tool calls.
6. Record observable facts and concise decision summaries, never hidden reasoning.

## Checks

- Loops have maximum steps, duration, retries, and request budget.
- External writes always require explicit approval.
- Retrieved content cannot authorize a tool.
- Provider failures, invalid output, timeout, and budget exhaustion are tested.

## Commands

Run `cd backend`; `python -m pytest tests/test_foundations.py`; then the full offline suite.

## Expected output

Deliver bounded runtime code, typed tools, approval decisions, trace examples, tests, and limitations.

## Stop conditions

Stop before an unbounded loop, untyped tool, hidden external write, raw model-to-database path, or trace containing sensitive reasoning/content.
