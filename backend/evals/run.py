from __future__ import annotations

import json
from pathlib import Path

from app.schemas.intake import IntakeResponse
from app.workflows.adaptive_recovery import diagnose_recovery
from app.workflows.intake import validate_intake_output

ROOT = Path(__file__).parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def plan_valid(case):
    start, end = case["candidate"]
    valid = case["working"][0] <= start < end <= case["working"][1]
    if case["protected"]:
        valid = valid and not (start < case["protected"][1] and end > case["protected"][0])
    for other_start, other_end in case["existing"]:
        valid = valid and not (start - case["buffer"] < other_end and end + case["buffer"] > other_start)
    return valid


def evaluate():
    intake = load("intake_extraction.json")
    valid_schema = deadline_correct = 0
    for case in intake:
        result = IntakeResponse.model_validate({"drafts": case["output"]["drafts"], "questions": case["output"]["questions"]})
        result = validate_intake_output(result, case["input"])
        valid_schema += int(len(result.drafts) == case["expected_count"] and [item.kind for item in result.drafts] == case["expected_kinds"])
        deadline_correct += int(any(item.deadline_at for item in result.drafts) == case["deadline_present"])
    clarification = load("clarification_quality.json")
    tp = fp = 0
    for case in clarification:
        expected, selected = set(case["expected_necessary"]), set(case["question_fields"])
        tp += len(expected & selected); fp += len(selected - expected)
    planning = load("planning_validity.json")
    accepted = [case for case in planning if plan_valid(case)]
    recovery = load("recovery_diagnosis.json")
    recovery_correct = sum(diagnose_recovery(case["commitment"], case["reflections"], over_capacity=case["over_capacity"], calendar_state=case["calendar_state"]) == case["expected"] for case in recovery)
    unsupported = load("unsupported_claims.json")
    unsupported_errors = 0
    for case in unsupported:
        output = {"drafts": [{"title":"Fixture","type":"hard_deadline","importance":3,"flexibility":3,"confidence_score":.9,"source_text":case["source_text"],"tasks":[],"missing_fields":[]}],"questions":[]}
        kept = validate_intake_output(IntakeResponse.model_validate(output), case["input"]).drafts[0].source_text is not None
        unsupported_errors += int(kept != case["expected_preserved"])
    tools = load("tool_selection.json")
    tool_correct = sum((case["selected"] in case["allowed"]) == case["expected_valid"] for case in tools)
    return {
        "dataset_sizes": {"intake": len(intake), "clarification": len(clarification), "planning": len(planning), "recovery": len(recovery), "unsupported_claims": len(unsupported), "tool_selection": len(tools)},
        "schema_valid_rate": valid_schema / len(intake),
        "deadline_extraction_accuracy": deadline_correct / len(intake),
        "clarification_precision": tp / max(1, tp + fp),
        "valid_plan_rate": sum(plan_valid(case) == case["expected_valid"] for case in planning) / len(planning),
        "overlap_violation_rate": sum(not plan_valid(case) for case in accepted) / max(1, len(accepted)),
        "recovery_diagnosis_accuracy": recovery_correct / len(recovery),
        "unsupported_claim_rate": unsupported_errors / len(unsupported),
        "tool_selection_accuracy": tool_correct / len(tools),
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True))
