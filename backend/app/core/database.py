import logging
from typing import Optional
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

supabase_client: Optional[Client] = None

# The backend is trusted server-side code. Prefer the service role key when present
# so RLS does not break internal persistence during the temporary DEV_USER_ID phase.
# Frontend code must never receive or use SUPABASE_SERVICE_ROLE_KEY.
supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY

if settings.SUPABASE_URL and supabase_key:
    try:
        supabase_client = create_client(settings.SUPABASE_URL, supabase_key)
        logger.info(
            "Supabase client initialized with %s key.",
            "service_role" if settings.SUPABASE_SERVICE_ROLE_KEY else "anon",
        )
    except Exception as e:
        logger.error("Failed to initialize Supabase client: %s", str(e))
else:
    logger.warning("Supabase environment variables are missing. Client not initialized.")
