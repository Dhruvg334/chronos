from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    ENV: str = "development"
    PORT: int = 8000
    
    # Provider-neutral model configuration. Model identifiers never belong in domain code.
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL_FAST: str = ""
    GROQ_MODEL_REASONING: str = ""
    GROQ_MODEL_TOOL_USE: str = ""
    MODEL_REQUEST_TIMEOUT_SECONDS: float = 20.0
    MODEL_MAX_RETRIES: int = 1
    WORKFLOW_MAX_STEPS: int = 6
    WORKFLOW_TIMEOUT_SECONDS: float = 45.0
    WORKFLOW_REQUEST_BUDGET: int = 4

    # Provider-neutral embeddings. The local hash provider is an offline fallback,
    # while Hugging Face can be enabled explicitly for semantic embeddings.
    EMBEDDING_PROVIDER: str = "local_hash"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str = "https://api-inference.huggingface.co/pipeline/feature-extraction"
    EMBEDDING_DIMENSIONS: int = 384
    EMBEDDING_REQUEST_TIMEOUT_SECONDS: float = 20.0
    EMBEDDING_MAX_RETRIES: int = 1
    KNOWLEDGE_MAX_FILE_BYTES: int = 5_000_000
    CONTEXT_PACK_TOKEN_BUDGET: int = 1800
    
    # Supabase Connection Keys
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/google/auth/callback"
    GOOGLE_SCOPES: str = "https://www.googleapis.com/auth/calendar.readonly"
    FRONTEND_URL: str = "http://localhost:5173"
    GOOGLE_OAUTH_STATE_SECRET: str = ""
    GMAIL_CLIENT_ID: str = ""
    GMAIL_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    NOTION_CLIENT_ID: str = ""
    NOTION_CLIENT_SECRET: str = ""
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    MICROSOFT_TENANT_ID: str = "common"
    INTEGRATION_REQUEST_TIMEOUT_SECONDS: float = 15.0
    INTEGRATION_MAX_RETRIES: int = 1
    INTEGRATION_MAX_PAGES: int = 10
    MCP_ALLOWED_SERVERS: List[str] = []
    MCP_REQUEST_TIMEOUT_SECONDS: float = 10.0
    MCP_REQUEST_BUDGET: int = 4
    MODEL_CALLS_PER_HOUR_USER: int = 30
    MODEL_CALLS_PER_HOUR_GLOBAL: int = 1000
    EMBEDDING_CALLS_PER_HOUR_USER: int = 60
    EMBEDDING_CALLS_PER_HOUR_GLOBAL: int = 3000
    INGESTION_REQUESTS_PER_HOUR_USER: int = 12
    INGESTION_BYTES_PER_HOUR_USER: int = 25_000_000
    INTEGRATION_SYNCS_PER_HOUR_USER: int = 12
    MCP_CALLS_PER_HOUR_USER: int = 60
    PROPOSALS_PER_HOUR_USER: int = 40
    FAILED_APPROVALS_PER_HOUR_USER: int = 10
    
    # Encryption key (32-byte url-safe base64 string)
    ENCRYPTION_KEY: str = ""
    
    # CORS Origins allowed
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # default Vite dev port
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]
    # Optional anchored regex for intentionally enabled deploy-preview origins.
    BACKEND_CORS_ORIGIN_REGEX: Optional[str] = None
    BACKEND_ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "testserver"]

    @field_validator("BACKEND_CORS_ORIGIN_REGEX")
    @classmethod
    def validate_preview_regex(cls, value: Optional[str]) -> Optional[str]:
        from app.core.security import is_safe_cors_regex
        if not is_safe_cors_regex(value):
            raise ValueError("CORS origin regex must be an anchored HTTPS pattern without broad wildcards")
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
