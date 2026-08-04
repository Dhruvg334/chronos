from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class EmbeddingResult:
    vectors: list[list[float]]
    provider: str
    model: str
    dimensions: int


class EmbeddingGateway(Protocol):
    async def embed(self, texts: Sequence[str]) -> EmbeddingResult: ...
    def metadata(self) -> dict[str, str | int]: ...
