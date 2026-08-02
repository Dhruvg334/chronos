from __future__ import annotations

from typing import Sequence, TypeVar

from pydantic import BaseModel

from app.models.gateway import ModelRequest, ModelResponse, ProviderHealth, ProviderStatus, StructuredResponse, ToolDefinition, ToolPlan

T = TypeVar("T", bound=BaseModel)


class FakeModelGateway:
    def __init__(self, *, text: str = "", structured: BaseModel | None = None, tool_plan: ToolPlan | None = None):
        self.text = text
        self.structured = structured
        self.tool_plan = tool_plan
        self.calls: list[ModelRequest] = []

    async def generate_text(self, request: ModelRequest) -> ModelResponse:
        self.calls.append(request)
        return ModelResponse(self.text, "fake", "deterministic")

    async def generate_structured(self, request: ModelRequest, schema: type[T]) -> StructuredResponse[T]:
        self.calls.append(request)
        if self.structured is None or not isinstance(self.structured, schema):
            raise ValueError(f"Fake response is not an instance of {schema.__name__}.")
        return StructuredResponse(self.structured, "fake", "deterministic")

    async def select_tools(self, request: ModelRequest, tools: Sequence[ToolDefinition]) -> ToolPlan:
        self.calls.append(request)
        return self.tool_plan or ToolPlan(None, {}, "No fake tool configured.", "fake", "deterministic")

    async def health(self) -> ProviderStatus:
        return ProviderStatus("fake", ProviderHealth.READY, True, "deterministic")

    def metadata(self) -> dict[str, str]:
        return {"provider": "fake", "model": "deterministic"}
