"""Compatibility boundary for paths not yet migrated to repository injection.

The facade contains no live client and performs no work during import. New code must
depend on repository protocols or FastAPI dependencies instead of importing this name.
"""
from typing import Any

from app.core.config import settings
from app.core.container import container


class _LazyDatabaseFacade:
    _is_coroutine_marker = None
    _is_coroutine = None

    def __bool__(self) -> bool:
        return bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__"):
            raise AttributeError(name)
        return getattr(container.database(), name)


supabase_client = _LazyDatabaseFacade()
