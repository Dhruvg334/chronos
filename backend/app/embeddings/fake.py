from __future__ import annotations

from collections.abc import Sequence

from app.embeddings.gateway import EmbeddingResult


class FakeEmbeddingGateway:
    def __init__(self, dimensions: int = 384, *, fail: Exception | None = None):
        self.dimensions = dimensions
        self.fail = fail
        self.calls: list[list[str]] = []

    async def embed(self, texts: Sequence[str]) -> EmbeddingResult:
        self.calls.append(list(texts))
        if self.fail:
            raise self.fail
        vectors = []
        for text in texts:
            vector = [0.0] * self.dimensions
            vector[sum(text.encode("utf-8")) % self.dimensions] = 1.0
            vectors.append(vector)
        return EmbeddingResult(vectors, "fake", "deterministic", self.dimensions)

    def metadata(self) -> dict[str, str | int]:
        return {"provider": "fake", "model": "deterministic", "dimensions": self.dimensions}
