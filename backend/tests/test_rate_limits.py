import pytest

from app.core.errors import ChronosError, ErrorCode
from app.services.usage_limits import Limit, UsageCategory, UsageLimiter


class FakeOperations:
    def __init__(self): self.used = 0; self.calls = 0
    def consume_budget(self, user_id, category, user_limit, global_limit, units=1):
        self.calls += 1
        if self.used + units > user_limit:
            return {"allowed": False, "retry_after_seconds": 42}
        self.used += units
        return {"allowed": True, "retry_after_seconds": 0}


def test_limit_is_enforced_before_caller_can_invoke_provider():
    repo = FakeOperations(); limiter = UsageLimiter(repo, {UsageCategory.MODEL: Limit(1, 5)})
    limiter.enforce("user-a", UsageCategory.MODEL)
    with pytest.raises(ChronosError) as error:
        limiter.enforce("user-a", UsageCategory.MODEL)
    assert error.value.code == ErrorCode.RATE_LIMITED
    assert error.value.failure_code == "rate_limited"
    assert error.value.context["retry_after_seconds"] == 42
    assert repo.calls == 2


def test_ingestion_units_are_counted_deterministically():
    repo = FakeOperations(); limiter = UsageLimiter(repo, {UsageCategory.INGESTION_BYTES: Limit(10, 100)})
    limiter.enforce("user-a", UsageCategory.INGESTION_BYTES, 10)
    with pytest.raises(ChronosError): limiter.enforce("user-a", UsageCategory.INGESTION_BYTES, 1)
