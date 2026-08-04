from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.core.errors import ChronosError, ErrorCode
from app.core.failures import FailureCode
from app.core.observability import metrics, request_id_context
from app.repositories.protocols import OperationalRepository
from app.core.config import settings


class UsageCategory(StrEnum):
    MODEL = "model_calls"
    EMBEDDING = "embedding_calls"
    INGESTION_BYTES = "ingestion_bytes"
    INGESTION = "ingestion_requests"
    INTEGRATION_SYNC = "integration_sync"
    MCP = "mcp_calls"
    PROPOSAL = "proposal_generation"
    FAILED_APPROVAL = "failed_approvals"


@dataclass(frozen=True)
class Limit:
    user: int
    global_: int


class UsageLimiter:
    def __init__(self, repository: OperationalRepository, limits: dict[UsageCategory, Limit]):
        self.repository = repository
        self.limits = limits

    def enforce(self, user_id: str, category: UsageCategory, units: int = 1) -> dict[str, object]:
        limit = self.limits[category]
        result = self.repository.consume_budget(user_id, category.value, limit.user, limit.global_, units)
        if not result.get("allowed"):
            metrics.increment("usage_budget_denied_total", category=category.value)
            raise ChronosError(ErrorCode.RATE_LIMITED, "This action has been used frequently. Please try again shortly.", context={
                "failure_code": FailureCode.RATE_LIMITED.value,
                "retry_after_seconds": int(result.get("retry_after_seconds", 60)),
                "category": category.value,
            })
        metrics.increment("usage_budget_consumed_total", category=category.value)
        return result


DEFAULT_LIMITS = {
    UsageCategory.MODEL: Limit(settings.MODEL_CALLS_PER_HOUR_USER, settings.MODEL_CALLS_PER_HOUR_GLOBAL),
    UsageCategory.EMBEDDING: Limit(settings.EMBEDDING_CALLS_PER_HOUR_USER, settings.EMBEDDING_CALLS_PER_HOUR_GLOBAL),
    UsageCategory.INGESTION: Limit(settings.INGESTION_REQUESTS_PER_HOUR_USER, 500),
    UsageCategory.INGESTION_BYTES: Limit(settings.INGESTION_BYTES_PER_HOUR_USER, 1_000_000_000),
    UsageCategory.INTEGRATION_SYNC: Limit(settings.INTEGRATION_SYNCS_PER_HOUR_USER, 1000),
    UsageCategory.MCP: Limit(settings.MCP_CALLS_PER_HOUR_USER, 5000),
    UsageCategory.PROPOSAL: Limit(settings.PROPOSALS_PER_HOUR_USER, 3000),
    UsageCategory.FAILED_APPROVAL: Limit(settings.FAILED_APPROVALS_PER_HOUR_USER, 1000),
}


def enforce_if_available(repository: OperationalRepository | None, user_id: str, category: UsageCategory, units: int = 1) -> None:
    if repository is not None:
        UsageLimiter(repository, DEFAULT_LIMITS).enforce(user_id, category, units)
