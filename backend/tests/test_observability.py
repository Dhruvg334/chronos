import json
import logging

from app.core.observability import NoOpMetrics, configure_metrics, log_event, redact


def test_redaction_blocks_secrets_and_raw_private_payloads(caplog):
    caplog.set_level(logging.INFO)
    log_event(logging.getLogger("test"), logging.INFO, "safe", api_key="secret", raw_email_body="private", count=2)
    payload = json.loads(caplog.records[-1].message)
    assert payload["api_key"] == "[REDACTED]"
    assert payload["raw_email_body"] == "[REDACTED]"
    assert "secret" not in caplog.records[-1].message


def test_default_metrics_adapter_is_local_safe_noop():
    sink = NoOpMetrics()
    configure_metrics(sink)
    sink.increment("provider_calls", provider="fake")
    sink.observe("latency_ms", 1.2, provider="fake")


def test_long_values_are_bounded():
    assert str(redact("x" * 1000)).endswith("[TRUNCATED]")
