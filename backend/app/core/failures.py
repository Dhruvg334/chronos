from __future__ import annotations

from enum import StrEnum

from app.core.errors import ErrorCode


class FailureCode(StrEnum):
    PROVIDER_TIMEOUT = "provider_timeout"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    RATE_LIMITED = "rate_limited"
    SCHEMA_INVALID = "schema_invalid"
    REPAIR_EXHAUSTED = "repair_exhausted"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    MISSING_CONTEXT = "missing_context"
    STALE_CONTEXT = "stale_context"
    OWNERSHIP_VIOLATION = "ownership_violation"
    CAPACITY_VIOLATION = "capacity_violation"
    OVERLAP_VIOLATION = "overlap_violation"
    DEPENDENCY_VIOLATION = "dependency_violation"
    PERMISSION_DENIED = "permission_denied"
    APPROVAL_REQUIRED = "approval_required"
    INTEGRATION_REVOKED = "integration_revoked"
    INTEGRATION_DEGRADED = "integration_degraded"
    RETRIEVAL_UNAVAILABLE = "retrieval_unavailable"
    TRANSACTION_ROLLBACK = "transaction_rollback"
    INTERNAL_DEFECT = "internal_defect"


DEFAULT_FAILURE_BY_ERROR: dict[ErrorCode, FailureCode] = {
    ErrorCode.VALIDATION: FailureCode.SCHEMA_INVALID,
    ErrorCode.AUTHENTICATION: FailureCode.PERMISSION_DENIED,
    ErrorCode.AUTHORIZATION: FailureCode.PERMISSION_DENIED,
    ErrorCode.CONFIGURATION: FailureCode.PROVIDER_UNAVAILABLE,
    ErrorCode.EXTERNAL_UNAVAILABLE: FailureCode.PROVIDER_UNAVAILABLE,
    ErrorCode.RATE_LIMITED: FailureCode.RATE_LIMITED,
    ErrorCode.PERSISTENCE: FailureCode.TRANSACTION_ROLLBACK,
    ErrorCode.CONFLICT: FailureCode.OVERLAP_VIOLATION,
    ErrorCode.MODEL_OUTPUT_INVALID: FailureCode.REPAIR_EXHAUSTED,
    ErrorCode.WORKFLOW_FAILED: FailureCode.INTERNAL_DEFECT,
}


def classify_error(error: ErrorCode, context: dict[str, object] | None = None) -> FailureCode:
    value = (context or {}).get("failure_code")
    if value:
        try:
            return FailureCode(str(value))
        except ValueError:
            pass
    return DEFAULT_FAILURE_BY_ERROR[error]
