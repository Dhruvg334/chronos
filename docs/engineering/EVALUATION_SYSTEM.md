# Evaluation system

ChronOS evaluation is provider-neutral. `backend/evals/framework.py` defines versioned datasets, per-case results, human labels, evaluator and prompt/model versions, aggregate metrics with explicit numerators and denominators, failure categories, and regression comparison. Deterministic evaluators are the release gate. Optional model evaluators may add review signals but cannot replace feasibility, ownership, or permission checks.

The hardening v1 corpus contains 105 manually reviewed synthetic cases: intake 20, daily planning 15, weekly planning 10, recovery 15, retrieval 15, memory proposals 10, tool permissions 10, and external proposals 10. It contains ambiguity, conflicts, impossible schedules, blocked work, stale and missing context, injection attempts, provider outages, and ownership attacks. It contains no production-derived data and is not evidence of production-level quality.

Runs record dataset version and digest, evaluator version, optional model and prompt versions, run metadata, case results, aggregate metrics, and failures. Domain evaluators report intake, planning, recovery, retrieval, tool, and proposal measures with sample size. A regression is a metric change beyond its configured tolerance against the same dataset.

Model-assisted evaluation is opt-in and uses redacted inputs, bounded requests, an evaluator version, and a disclosed model version. Raw prompts, provider responses, hidden reasoning, email bodies, and full documents are not evaluation telemetry.
