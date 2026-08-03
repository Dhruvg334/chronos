import logging

import httpx
import pytest
from pydantic import BaseModel

from app.core.errors import ChronosError, ErrorCode
from app.models.gateway import ModelRequest
from app.models.groq import GroqModelGateway


class Result(BaseModel):
    value: int


class StubClient:
    queue = []
    requests = []

    def __init__(self, **_kwargs): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *_args): return None
    async def post(self, url, *, headers, json):
        self.requests.append({"url": url, "headers": headers, "json": json})
        item = self.queue.pop(0)
        if isinstance(item, Exception): raise item
        return item


def response(status: int, payload=None, headers=None):
    request = httpx.Request("POST", "https://api.groq.test/chat/completions")
    return httpx.Response(status, json=payload or {}, headers=headers, request=request)


@pytest.fixture
def gateway(monkeypatch):
    StubClient.queue, StubClient.requests = [], []
    monkeypatch.setattr("app.models.groq.httpx.AsyncClient", StubClient)
    return GroqModelGateway(api_key="secret-key", base_url="https://api.groq.test", models={"fast": "fast", "reasoning": "reason", "tool_use": "tool"}, timeout=.01, max_retries=1)


@pytest.mark.anyio
async def test_structured_response_and_one_bounded_repair(gateway):
    StubClient.queue.extend([
        response(200, {"choices": [{"message": {"content": "not json"}}]}),
        response(200, {"choices": [{"message": {"content": '{"value":7}'}}]}),
    ])
    result = await gateway.generate_structured(ModelRequest(prompt="private user wording"), Result)
    assert result.value.value == 7 and result.repair_attempts == 1
    assert len(StubClient.requests) == 2
    assert "private user wording" not in StubClient.requests[1]["json"]["messages"][-1]["content"]


@pytest.mark.anyio
async def test_invalid_model_response_stops_after_repair(gateway, caplog):
    StubClient.queue.extend([response(200, {"choices": [{"message": {"content": "x"}}]}), response(200, {"choices": [{"message": {"content": "y"}}]})])
    with caplog.at_level(logging.WARNING), pytest.raises(ChronosError) as raised:
        await gateway.generate_structured(ModelRequest(prompt="sensitive raw prompt"), Result)
    assert raised.value.code == ErrorCode.MODEL_OUTPUT_INVALID
    assert len(StubClient.requests) == 2
    assert "sensitive raw prompt" not in caplog.text and "secret-key" not in caplog.text


@pytest.mark.anyio
async def test_timeout_and_server_failure_retry_once(gateway):
    StubClient.queue.extend([httpx.ReadTimeout("slow"), response(503), response(200, {"choices": [{"message": {"content": "ok"}}]})])
    with pytest.raises(ChronosError) as timeout:
        await gateway.generate_text(ModelRequest(prompt="one"))
    assert timeout.value.code == ErrorCode.EXTERNAL_UNAVAILABLE
    StubClient.queue.clear()
    StubClient.queue.extend([response(503), response(200, {"choices": [{"message": {"content": "ok"}}]})])
    result = await gateway.generate_text(ModelRequest(prompt="two"))
    assert result.text == "ok"


@pytest.mark.anyio
async def test_rate_limit_is_classified_without_unbounded_retry(gateway):
    StubClient.queue.append(response(429, {"error": {"message": "busy"}}, {"retry-after": "2"}))
    with pytest.raises(ChronosError) as raised:
        await gateway.generate_text(ModelRequest(prompt="x"))
    assert raised.value.code == ErrorCode.RATE_LIMITED
    assert raised.value.context["retry_after_seconds"] == "2"
    assert len(StubClient.requests) == 1


@pytest.mark.anyio
async def test_unconfigured_provider_health_and_request():
    gateway = GroqModelGateway(api_key="", base_url="https://api.groq.test", models={"fast": ""}, timeout=.01, max_retries=0)
    assert (await gateway.health()).state == "unconfigured"
    with pytest.raises(ChronosError) as raised:
        await gateway.generate_text(ModelRequest(prompt="x"))
    assert raised.value.code == ErrorCode.CONFIGURATION
