from evals.context_run import evaluate_context


def test_context_evaluation_fixture_metrics_are_deterministic():
    metrics = evaluate_context()
    assert metrics["dataset_sizes"] == {"documents": 10, "queries": 12, "memory_cases": 8, "duplicate_cases": 6, "pack_cases": 6}
    assert metrics["recall_at_3"] >= .9
    assert metrics["mrr"] >= .85
    assert metrics["ndcg_at_3"] >= .85
    assert metrics["citation_accuracy"] >= .9
    assert metrics["ownership_leakage_rate"] == 0
    assert metrics["unsupported_memory_rate"] == 0
    assert metrics["duplicate_ingestion_error_rate"] == 0
    assert metrics["token_budget_compliance"] == 1
    assert metrics["prompt_injection_instruction_execution_rate"] == 0
