from __future__ import annotations

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    VALIDATION = "validation_error"
    AUTHENTICATION = "authentication_error"
    AUTHORIZATION = "authorization_error"
    CONFIGURATION = "configuration_error"
    EXTERNAL_UNAVAILABLE = "external_service_unavailable"
    RATE_LIMITED = "rate_limited"
    PERSISTENCE = "persistence_error"
    CONFLICT = "conflict"
    MODEL_OUTPUT_INVALID = "model_output_invalid"
    WORKFLOW_FAILED = "workflow_failed"


class ChronosError(Exception):
    def __init__(self, code: ErrorCode, public_message: str, *, context: dict[str, Any] | None = None):
        super().__init__(public_message)
        self.code = code
        self.public_message = public_message
        self.context = context or {}


HTTP_STATUS_BY_ERROR = {
    ErrorCode.VALIDATION: 422,
    ErrorCode.AUTHENTICATION: 401,
    ErrorCode.AUTHORIZATION: 403,
    ErrorCode.CONFIGURATION: 503,
    ErrorCode.EXTERNAL_UNAVAILABLE: 503,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.PERSISTENCE: 503,
    ErrorCode.CONFLICT: 409,
    ErrorCode.MODEL_OUTPUT_INVALID: 422,
    ErrorCode.WORKFLOW_FAILED: 500,
}
