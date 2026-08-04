from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
