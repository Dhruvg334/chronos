from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Callable, Protocol


class DatasetOrigin(StrEnum):
    SYNTHETIC = "synthetic"
    MANUALLY_CURATED = "manually_curated"
    PRODUCTION_DERIVED = "production_derived"


@dataclass(frozen=True)
class EvalCase:
    id: str
    input: dict[str, Any]
    expected: dict[str, Any]
    tags: tuple[str, ...] = ()
    human_label: str | None = None


@dataclass(frozen=True)
class Dataset:
    name: str
    version: str
    origin: DatasetOrigin
    cases: tuple[EvalCase, ...]
    limitations: str

    @property
    def digest(self) -> str:
        payload = [{"id": c.id, "input": c.input, "expected": c.expected} for c in self.cases]
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    passed: bool
    metrics: dict[str, tuple[int, int]]
    failure_codes: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvalRun:
    dataset: str
    dataset_version: str
    dataset_digest: str
    evaluator_version: str
    model_version: str | None
    prompt_version: str | None
    run_metadata: dict[str, str]
    case_results: tuple[CaseResult, ...]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def aggregate(self) -> dict[str, dict[str, float | int]]:
        totals: dict[str, list[int]] = {}
        for result in self.case_results:
            for name, (numerator, denominator) in result.metrics.items():
                pair = totals.setdefault(name, [0, 0])
                pair[0] += numerator; pair[1] += denominator
        return {name: {"value": num / den if den else 0.0, "numerator": num, "denominator": den}
                for name, (num, den) in totals.items()}


class OptionalModelEvaluator(Protocol):
    async def score(self, case: EvalCase, actual: dict[str, Any]) -> dict[str, float]: ...


def run_deterministic(dataset: Dataset, evaluator: Callable[[EvalCase], CaseResult], *,
                      evaluator_version: str, model_version: str | None = None,
                      prompt_version: str | None = None, metadata: dict[str, str] | None = None) -> EvalRun:
    return EvalRun(dataset.name, dataset.version, dataset.digest, evaluator_version, model_version,
                   prompt_version, metadata or {}, tuple(evaluator(case) for case in dataset.cases))


def compare_runs(current: EvalRun, baseline: EvalRun, tolerances: dict[str, float] | None = None) -> dict[str, Any]:
    if current.dataset != baseline.dataset:
        raise ValueError("regression comparison requires the same dataset")
    tolerances = tolerances or {}
    current_metrics, baseline_metrics = current.aggregate(), baseline.aggregate()
    changes = {}
    for name, metric in current_metrics.items():
        prior = float(baseline_metrics.get(name, {"value": 0})["value"])
        delta = float(metric["value"]) - prior
        changes[name] = {"baseline": prior, "current": metric["value"], "delta": delta,
                         "regression": delta < -abs(tolerances.get(name, 0.0))}
    return {"dataset": current.dataset, "baseline_version": baseline.dataset_version,
            "current_version": current.dataset_version, "changes": changes}
