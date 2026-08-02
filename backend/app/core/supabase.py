from supabase import Client

from app.core.container import container


def get_supabase_client() -> Client:
    """Return the application-owned client, creating it only on first use."""
    return container.database()
