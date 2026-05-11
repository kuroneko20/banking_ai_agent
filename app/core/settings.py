"""
Application settings using Pydantic Settings.
All configuration is loaded from environment variables or .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Global application settings."""

    # Ollama configuration
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    model_name: str = Field(default="gpt-oss:20b", alias="MODEL_NAME")
    ollama_timeout: float = Field(default=120.0, alias="OLLAMA_TIMEOUT")

    # API server configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_title: str = "Banking AI-Agent"
    api_version: str = "1.0.0"

    # Agent configuration
    min_intent_confidence: float = Field(default=0.4, alias="MIN_INTENT_CONFIDENCE")
    min_validation_score: float = Field(default=0.5, alias="MIN_VALIDATION_SCORE")
    min_response_length: int = Field(default=20, alias="MIN_RESPONSE_LENGTH")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = {"env_file": ".env", "populate_by_name": True, "protected_namespaces": ("settings_",)}


# Singleton instance
settings = Settings()
