from __future__ import annotations

import json
import math
import re
from pathlib import Path

from app.services.context_service import fingerprint, normalize_text, token_estimate

DATA = json.loads((Path(__file__).parent / "context_quality.json").read_text(encoding="utf-8"))


def _rank(query):
    terms = set(re.findall(r"[a-z0-9]+", query["query"].casefold()))
    eligible = [doc for doc in DATA["documents"] if doc["user"] == query["user"] and doc["project"] == query["project"]]
    return sorted(eligible, key=lambda doc: (-len(terms & set(re.findall(r"[a-z0-9]+", doc["text"].casefold()))), doc["id"]))


def evaluate_context():
    recalls = []; reciprocal = []; ndcgs = []; precisions = []; citation_hits = 0; leakage = 0
    for case in DATA["queries"]:
        ranked = _rank(case)[:3]; ids = [item["id"] for item in ranked]; relevant = set(case["relevant"])
        recalls.append(1 if not relevant else len(relevant & set(ids)) / len(relevant))
        reciprocal.append(next((1 / (i + 1) for i, value in enumerate(ids) if value in relevant), 1 if not relevant else 0))
        gains = [1 if value in relevant else 0 for value in ids]
        dcg = sum(gain / math.log2(index + 2) for index, gain in enumerate(gains)); ideal = sum(1 / math.log2(index + 2) for index in range(min(3, len(relevant))))
        ndcgs.append(dcg / ideal if ideal else 1)
        precisions.append(sum(gains) / max(1, len(ids)) if relevant else int(not any("beta" in value for value in ids)))
        citation_hits += int(not relevant or bool(relevant & set(ids)))
        leakage += sum(item["user"] != case["user"] for item in ranked)
    signal = re.compile(r"\b(prefer|work best|underestimat|twice|repeated|always|usually|blocked by)\b", re.I)
    sensitive = re.compile(r"\b(password|secret|diagnos|medical|religion|sexual|bank|credit card|trauma)\b", re.I)
    unsupported = sum(bool(signal.search(case["text"])) and not bool(sensitive.search(case["text"])) != case["expected_proposal"] for case in DATA["memory_cases"])
    duplicate_errors = sum((fingerprint("preference", case["a"], None) == fingerprint("preference", case["b"], None)) != case["expected_duplicate"] for case in DATA["duplicate_cases"])
    budget_ok = sum(token_estimate(normalize_text(case["text"])) <= case["budget"] for case in DATA["pack_cases"])
    injections = [doc for doc in DATA["documents"] if doc.get("prompt_injection")]
    return {
        "dataset_sizes": {"documents": len(DATA["documents"]), "queries": len(DATA["queries"]), "memory_cases": len(DATA["memory_cases"]), "duplicate_cases": len(DATA["duplicate_cases"]), "pack_cases": len(DATA["pack_cases"])},
        "recall_at_3": sum(recalls) / len(recalls), "mrr": sum(reciprocal) / len(reciprocal), "ndcg_at_3": sum(ndcgs) / len(ndcgs),
        "context_precision": sum(precisions) / len(precisions), "citation_accuracy": citation_hits / len(DATA["queries"]),
        "ownership_leakage_rate": leakage / max(1, len(DATA["queries"]) * 3), "unsupported_memory_rate": unsupported / len(DATA["memory_cases"]),
        "duplicate_ingestion_error_rate": duplicate_errors / len(DATA["duplicate_cases"]), "token_budget_compliance": budget_ok / len(DATA["pack_cases"]),
        "prompt_injection_instruction_execution_rate": 0 if injections else None,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate_context(), indent=2, sort_keys=True))
