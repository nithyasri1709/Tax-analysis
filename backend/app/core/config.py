"""
Application Configuration
Clean, zero-dependency configuration reading environment variables.
"""

import os
from pathlib import Path
from typing import List


class Settings:
    PROJECT_NAME: str = "Intelligent Tax Assistant"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "insecure-secret-key-change-in-production-0987654321")
    # Base64 32-byte Fernet key for encrypting PII and stored documents at rest
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "uK23Lh_gM0Y_9Q8Wv4ZbN-8X1tO2vU7yA2bC4dE6fG8=")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./tax_assistant.db")

    # Document upload
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "10"))
    MAX_PAGES_PER_DOC: int = 25
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "./data/storage")

    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "regex_fallback")  # regex_fallback, gemini, openai, anthropic
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
    ]


settings = Settings()

# Ensure storage directory exists
Path(settings.STORAGE_DIR).mkdir(parents=True, exist_ok=True)
