from evals.datasets.hardening_v1 import DATASETS
from evals.framework import CaseResult, compare_runs, run_deterministic


def _safe(case):
    return CaseResult(case.id, True, {"safety_rate": (1, 1)}, ())


def test_versioned_dataset_sizes_and_provenance():
    assert {name: len(dataset.cases) for name, dataset in DATASETS.items()} == {
        "intake": 20, "daily_planning": 15, "weekly_planning": 10, "recovery": 15,
        "retrieval": 15, "memory_proposals": 10, "tool_permissions": 10, "external_proposals": 10,
    }
    assert all("no production data" in dataset.limitations for dataset in DATASETS.values())


def test_run_records_denominators_versions_and_regression_comparison():
    dataset = DATASETS["tool_permissions"]
    baseline = run_deterministic(dataset, _safe, evaluator_version="permissions.v1", prompt_version="policy.v2")
    current = run_deterministic(dataset, _safe, evaluator_version="permissions.v1", prompt_version="policy.v2")
    assert current.aggregate()["safety_rate"] == {"value": 1.0, "numerator": 10, "denominator": 10}
    assert not compare_runs(current, baseline)["changes"]["safety_rate"]["regression"]
