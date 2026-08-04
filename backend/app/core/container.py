from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING

from supabase import Client, create_client

from app.core.config import settings

if TYPE_CHECKING:
    from app.embeddings.gateway import EmbeddingGateway
    from app.models.gateway import ModelGateway


class ApplicationContainer:
    """Own live service construction so imports remain deterministic and testable."""

    def __init__(self) -> None:
        self._database: Client | None = None
        self._model_gateway: ModelGateway | None = None
        self._embedding_gateway: EmbeddingGateway | None = None
        self._lock = Lock()

    def database(self) -> Client:
        if self._database is None:
            if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
                raise RuntimeError("Backend database configuration is incomplete.")
            with self._lock:
                if self._database is None:
                    self._database = create_client(
                        settings.SUPABASE_URL,
                        settings.SUPABASE_SERVICE_ROLE_KEY,
                    )
        return self._database

    def model_gateway(self) -> ModelGateway:
        if self._model_gateway is None:
            from app.models.groq import GroqModelGateway

            if settings.LLM_PROVIDER.lower() != "groq":
                raise RuntimeError(f"Unsupported model provider: {settings.LLM_PROVIDER}")
            self._model_gateway = GroqModelGateway.from_settings(settings)
        return self._model_gateway

    def embedding_gateway(self) -> EmbeddingGateway:
        if self._embedding_gateway is None:
            from app.embeddings.providers import HuggingFaceEmbeddingGateway, LocalHashEmbeddingGateway

            provider = settings.EMBEDDING_PROVIDER.lower()
            if provider == "local_hash":
                self._embedding_gateway = LocalHashEmbeddingGateway(dimensions=settings.EMBEDDING_DIMENSIONS)
            elif provider == "huggingface":
                self._embedding_gateway = HuggingFaceEmbeddingGateway.from_settings(settings)
            else:
                raise RuntimeError(f"Unsupported embedding provider: {settings.EMBEDDING_PROVIDER}")
        return self._embedding_gateway

    def reset_for_tests(self) -> None:
        self._database = None
        self._model_gateway = None
        self._embedding_gateway = None


container = ApplicationContainer()
