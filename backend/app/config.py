# backend/app/config.py
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields in .env
    )

    # Presenton Configuration
    presenton_api_url: str = "http://presenton:8000"
    presenton_api_key: str

    # Ollama Configuration
    # ollama_url: str = "http://localhost:11434" #home
    ollama_url: str = "http://192.168.68.51:11434" #office
    # ollama_model: str = "phi4-mini-reasoning:3.8b" #home
    ollama_model: str = "gpt-oss:20b" #office
    # Pexels Configuration
    pexels_api_key: str

    # Backend Configuration
    backend_port: int = 5000
    cors_origins: str = "*"
    debug: bool = True

    # File paths
    output_dir: str = "./output"

@lru_cache()
def get_settings() -> Settings:
    return Settings()