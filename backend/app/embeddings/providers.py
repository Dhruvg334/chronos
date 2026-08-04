from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence

import httpx

from app.core.errors import ChronosError, ErrorCode
from app.embeddings.gateway import EmbeddingResult


class LocalHashEmbeddingGateway:
    """Deterministic offline fallback; suitable for tests and lexical-assisted retrieval."""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    async def embed(self, texts: Sequence[str]) -> EmbeddingResult:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for token in text.casefold().split():
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "big") % self.dimensions
                vector[index] += -1.0 if digest[4] & 1 else 1.0
            norm = math.sqrt(sum(value * value for value in vector)) or 1.0
            vectors.append([value / norm for value in vector])
        return EmbeddingResult(vectors, "local_hash", "sha256-token-hash", self.dimensions)

    def metadata(self) -> dict[str, str | int]:
        return {"provider": "local_hash", "model": "sha256-token-hash", "dimensions": self.dimensions}


class HuggingFaceEmbeddingGateway:
    def __init__(self, *, api_key: str, base_url: str, model: str, dimensions: int, timeout: float, max_retries: int):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.dimensions = dimensions
        self.timeout = timeout
        self.max_retries = max(0, max_retries)

    @classmethod
    def from_settings(cls, settings):
        return cls(api_key=settings.EMBEDDING_API_KEY, base_url=settings.EMBEDDING_BASE_URL,
                   model=settings.EMBEDDING_MODEL, dimensions=settings.EMBEDDING_DIMENSIONS,
                   timeout=settings.EMBEDDING_REQUEST_TIMEOUT_SECONDS, max_retries=settings.EMBEDDING_MAX_RETRIES)

    async def embed(self, texts: Sequence[str]) -> EmbeddingResult:
        if not self.api_key:
            raise ChronosError(ErrorCode.CONFIGURATION, "The embedding provider is not configured.")
        if not texts or len(texts) > 64:
            raise ChronosError(ErrorCode.VALIDATION, "Embedding batches must contain between one and 64 items.")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/{self.model}"
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, headers=headers, json={"inputs": list(texts), "options": {"wait_for_model": True}})
                if response.status_code == 429:
                    raise ChronosError(ErrorCode.RATE_LIMITED, "The embedding provider is busy. Try again shortly.")
                if response.status_code in {500, 502, 503, 504} and attempt < self.max_retries:
                    continue
                response.raise_for_status()
                payload = response.json()
                vectors = self._normalize_payload(payload, len(texts))
                if any(len(vector) != self.dimensions for vector in vectors):
                    raise ChronosError(ErrorCode.MODEL_OUTPUT_INVALID, "The embedding provider returned an incompatible vector.")
                return EmbeddingResult(vectors, "huggingface", self.model, self.dimensions)
            except ChronosError:
                raise
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt >= self.max_retries:
                    raise ChronosError(ErrorCode.EXTERNAL_UNAVAILABLE, "The embedding provider is temporarily unavailable.") from exc
            except (httpx.HTTPStatusError, ValueError, TypeError) as exc:
                raise ChronosError(ErrorCode.EXTERNAL_UNAVAILABLE, "The embedding provider could not process this source.") from exc
        raise ChronosError(ErrorCode.EXTERNAL_UNAVAILABLE, "The embedding provider is temporarily unavailable.")

    @staticmethod
    def _normalize_payload(payload, expected: int) -> list[list[float]]:
        if not isinstance(payload, list):
            raise ValueError("invalid embedding payload")
        # Feature extraction may return token vectors; mean-pool those deterministically.
        if expected == 1 and payload and isinstance(payload[0], (int, float)):
            return [[float(value) for value in payload]]
        result: list[list[float]] = []
        for item in payload:
            if item and isinstance(item[0], list):
                result.append([sum(float(token[i]) for token in item) / len(item) for i in range(len(item[0]))])
            else:
                result.append([float(value) for value in item])
        if len(result) != expected:
            raise ValueError("embedding batch size mismatch")
        return result

    def metadata(self) -> dict[str, str | int]:
        return {"provider": "huggingface", "model": self.model, "dimensions": self.dimensions}
