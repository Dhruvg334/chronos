import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENV: str = "development"
    PORT: int = 8000
    
    # Gemini API Key & Models
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_FAST: str = "gemini-2.5-flash"
    GEMINI_MODEL_REASONING: str = "gemini-2.5-pro"
    GEMINI_MODEL_DEFAULT: str = "gemini-2.5-flash"
    
    # Supabase Connection Keys
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/calendar/callback"
    
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
