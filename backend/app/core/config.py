from typing import List
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
    
    # Encryption key (32-byte url-safe base64 string)
    ENCRYPTION_KEY: str = ""
    
    # CORS Origins allowed
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # default Vite dev port
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
