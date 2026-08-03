from evals.run import evaluate


def test_small_golden_evaluation_sets_are_deterministic():
    metrics = evaluate()
    assert metrics["dataset_sizes"] == {"intake": 5, "clarification": 5, "planning": 5, "recovery": 5, "unsupported_claims": 5, "tool_selection": 5}
    assert metrics["schema_valid_rate"] == 1
    assert metrics["deadline_extraction_accuracy"] == 1
    assert metrics["clarification_precision"] == 1
    assert metrics["valid_plan_rate"] == 1
    assert metrics["overlap_violation_rate"] == 0
    assert metrics["recovery_diagnosis_accuracy"] == 1
    assert metrics["unsupported_claim_rate"] == 0
    assert metrics["tool_selection_accuracy"] == 1
