# backend/app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Presenton Configuration
    presenton_api_url: str = "http://localhost:8000"
    presenton_api_key: str
    
    # Ollama Configuration
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "gpt-oss:20b"
    
    # Pexels Configuration
    pexels_api_key: str
    
    # Backend Configuration
    backend_port: int = 5000
    cors_origins: str = "*"
    debug: bool = True
    
    # File paths
    output_dir: str = "./output"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()