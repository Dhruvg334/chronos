from __future__ import annotations

import json
import logging
import asyncio
import time
from typing import Any, Sequence, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.errors import ChronosError, ErrorCode
from app.core.observability import log_event, metrics, record_dependency_state
from app.models.gateway import (
    ModelRequest,
    ModelResponse,
    ProviderHealth,
    ProviderStatus,
    StructuredResponse,
    ToolDefinition,
    ToolPlan,
)

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class GroqModelGateway:
    """Groq implementation over its OpenAI-compatible HTTPS API."""

    def __init__(self, *, api_key: str, base_url: str, models: dict[str, str], timeout: float, max_retries: int):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._models = models
        self._timeout = timeout
        self._max_retries = max(0, max_retries)

    @classmethod
    def from_settings(cls, settings):
        return cls(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
            models={
                "fast": settings.GROQ_MODEL_FAST,
                "reasoning": settings.GROQ_MODEL_REASONING,
                "tool_use": settings.GROQ_MODEL_TOOL_USE,
            },
            timeout=settings.MODEL_REQUEST_TIMEOUT_SECONDS,
            max_retries=settings.MODEL_MAX_RETRIES,
        )

    def _model(self, role: str) -> str:
        model = self._models.get(role) or self._models.get("fast")
        if not self._api_key or not model:
            raise ChronosError(ErrorCode.CONFIGURATION, "The model provider is not configured.")
        return model

    async def _completion(self, request: ModelRequest, *, extra: dict[str, Any] | None = None) -> tuple[dict[str, Any], str, float, int]:
        model = self._model(request.model_role)
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "max_completion_tokens": request.max_tokens,
        }
        body.update(extra or {})
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

        for attempt in range(self._max_retries + 1):
            started = time.perf_counter()
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(f"{self._base_url}/chat/completions", headers=headers, json=body)
                if response.status_code == 429:
                    retry_after = response.headers.get("retry-after")
                    raise ChronosError(
                        ErrorCode.RATE_LIMITED,
                        "The model provider is busy. Try again shortly.",
                        context={"provider": "groq", "retry_after_seconds": retry_after},
                    )
                if response.status_code == 400:
                    error = response.json().get("error", {})
                    if error.get("code") == "json_validate_failed":
                        raise ChronosError(
                            ErrorCode.MODEL_OUTPUT_INVALID,
                            "The model returned a response that failed schema validation.",
                            context={"provider": "groq", "failure": "json_validate_failed"},
                        )
                if response.status_code in {500, 502, 503, 504} and attempt < self._max_retries:
                    await asyncio.sleep(min(0.05 * (2 ** attempt), 0.5))
                    continue
                response.raise_for_status()
                latency = round((time.perf_counter() - started) * 1000, 2)
                metrics.increment("model_provider_calls_total", provider="groq", outcome="success")
                metrics.observe("model_provider_latency_ms", latency, provider="groq")
                record_dependency_state("model_provider", "reachable")
                return response.json(), model, latency, attempt + 1
            except ChronosError:
                raise
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt >= self._max_retries:
                    metrics.increment("model_provider_errors_total", provider="groq", failure="provider_unavailable")
                    record_dependency_state("model_provider", "unavailable")
                    log_event(logger, logging.WARNING, "model_unavailable", provider="groq", exception=type(exc).__name__)
                    raise ChronosError(
                        ErrorCode.EXTERNAL_UNAVAILABLE,
                        "The model provider is temporarily unavailable.",
                        context={"provider": "groq", "failure": "timeout_or_network"},
                    ) from exc
                await asyncio.sleep(min(0.05 * (2 ** attempt), 0.5))
            except (httpx.HTTPStatusError, ValueError) as exc:
                log_event(logger, logging.ERROR, "model_provider_error", provider="groq", exception=type(exc).__name__)
                raise ChronosError(ErrorCode.EXTERNAL_UNAVAILABLE, "The model provider could not complete the request.") from exc
        raise ChronosError(ErrorCode.EXTERNAL_UNAVAILABLE, "The model provider is temporarily unavailable.")

    async def generate_text(self, request: ModelRequest) -> ModelResponse:
        payload, model, latency, request_count = await self._completion(request)
        try:
            choice = payload["choices"][0]["message"]
            usage = {key: int(value) for key, value in (payload.get("usage") or {}).items() if isinstance(value, int)}
            return ModelResponse(text=choice.get("content") or "", provider="groq", model=model, request_id=payload.get("id"),
                prompt_version=request.prompt_version, schema_version=request.schema_version, latency_ms=latency,
                request_count=request_count, token_usage=usage)
        except (KeyError, IndexError, TypeError) as exc:
            raise ChronosError(ErrorCode.MODEL_OUTPUT_INVALID, "The model returned an invalid response.") from exc

    async def generate_structured(self, request: ModelRequest, schema: type[T]) -> StructuredResponse[T]:
        schema_payload = schema.model_json_schema()
        current = request
        for repair_attempt in range(2):
            try:
                payload, model, latency, request_count = await self._completion(
                    current,
                    extra={"response_format": {"type": "json_schema", "json_schema": {"name": schema.__name__, "strict": False, "schema": schema_payload}}},
                )
            except ChronosError as exc:
                if exc.code != ErrorCode.MODEL_OUTPUT_INVALID or repair_attempt == 1:
                    raise
                current = self._repair_request(request, schema_payload)
                continue
            try:
                raw = payload["choices"][0]["message"]["content"]
                value = schema.model_validate_json(raw)
                usage = {key: int(value) for key, value in (payload.get("usage") or {}).items() if isinstance(value, int)}
                metrics.increment("model_repairs_total", provider="groq", value=repair_attempt)
                return StructuredResponse(value=value, provider="groq", model=model, repair_attempts=repair_attempt,
                    prompt_version=request.prompt_version, schema_version=request.schema_version, latency_ms=latency,
                    request_count=request_count + repair_attempt, token_usage=usage)
            except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValidationError) as exc:
                if repair_attempt == 1:
                    log_event(logger, logging.WARNING, "model_validation_failed", schema=schema.__name__, error_count=len(exc.errors()) if isinstance(exc, ValidationError) else 1)
                    raise ChronosError(ErrorCode.MODEL_OUTPUT_INVALID, "The response needs clarification before it can be used.") from exc
                current = self._repair_request(request, schema_payload)
        raise ChronosError(ErrorCode.MODEL_OUTPUT_INVALID, "The response needs clarification before it can be used.")

    @staticmethod
    def _repair_request(request: ModelRequest, schema_payload: dict[str, Any]) -> ModelRequest:
        return ModelRequest(
            prompt=(
                "The previous response failed deterministic validation. Retry the original request and return only a corrected JSON object "
                f"that satisfies this schema: {json.dumps(schema_payload)}\n\nOriginal request:\n{request.prompt}"
            ),
            system_prompt="Repair the structured response without adding unsupported facts.",
            model_role="reasoning",
            max_tokens=request.max_tokens,
            temperature=0,
            metadata=request.metadata,
            prompt_version=request.prompt_version,
            schema_version=request.schema_version,
        )

    async def select_tools(self, request: ModelRequest, tools: Sequence[ToolDefinition]) -> ToolPlan:
        tool_request = ModelRequest(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            model_role="tool_use",
            max_tokens=request.max_tokens,
            temperature=0,
        )
        payload, model, _, _ = await self._completion(
            tool_request,
            extra={"tools": [{"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.input_schema}} for t in tools], "tool_choice": "auto"},
        )
        message = payload.get("choices", [{}])[0].get("message", {})
        calls = message.get("tool_calls") or []
        if not calls:
            return ToolPlan(None, {}, (message.get("content") or "No tool selected.")[:240], "groq", model)
        call = calls[0].get("function", {})
        try:
            arguments = json.loads(call.get("arguments") or "{}")
        except json.JSONDecodeError as exc:
            raise ChronosError(ErrorCode.MODEL_OUTPUT_INVALID, "The selected tool arguments were invalid.") from exc
        return ToolPlan(call.get("name"), arguments, "Selected a bounded tool based on the supplied context.", "groq", model)

    async def health(self) -> ProviderStatus:
        configured = bool(self._api_key and self._models.get("fast"))
        return ProviderStatus("groq", ProviderHealth.READY if configured else ProviderHealth.UNCONFIGURED, configured, "configured" if configured else "API key or fast model is missing")

    def metadata(self) -> dict[str, str]:
        return {"provider": "groq", "fast_model": self._models.get("fast", ""), "reasoning_model": self._models.get("reasoning", ""), "tool_model": self._models.get("tool_use", "")}
