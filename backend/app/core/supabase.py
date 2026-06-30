from supabase import create_client, Client

from app.core.config import settings


def get_supabase_client() -> Client:
    """Create a Supabase client for backend-only operations.

    Use the shared Settings object instead of reading os.environ directly. In
    local development, pydantic loads backend/.env for Settings, but raw
    os.getenv calls may not see those values. That made valid frontend Supabase
    sessions fail backend JWT validation with 401 responses.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in backend environment.")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
