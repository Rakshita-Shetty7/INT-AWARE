"""
Centralized Configuration Settings for Intent-Aware Deception System.
Loads environment variables safely using python-dotenv.
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load .env file from project root if present
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


class Settings:
    """
    Application configuration parameters.
    """
    # Google Gemini AI Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_TIMEOUT: float = float(os.getenv("GEMINI_TIMEOUT", "5.0"))
    GEMINI_ENABLED: bool = os.getenv("GEMINI_ENABLED", "true").lower() in ("true", "1", "yes")

    # Rule Engine Configuration
    RULE_ENGINE_ENABLED: bool = os.getenv("RULE_ENGINE_ENABLED", "true").lower() in ("true", "1", "yes")

    # Cowrie Honeypot Log Path
    COWRIE_LOG_PATH: str = os.getenv("COWRIE_LOG_PATH", "./honeypot/var/log/cowrie/cowrie.json")

    # Database Configuration
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "intent_deception_db")

    # API Server Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # CORS Allowed Origins
    CORS_ORIGINS_RAW: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000")
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS_RAW.split(",") if origin.strip()]


def is_gemini_api_key_configured(api_key: str) -> bool:
    """Return whether the configured value is an actual Gemini API key."""
    normalized_key = api_key.strip()
    return bool(normalized_key) and not normalized_key.lower().startswith(
        ("your_gemini_api_key", "your-api-key", "replace-with-")
    )


settings = Settings()
