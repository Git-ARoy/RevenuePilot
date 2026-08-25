import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Find .env at project root or current directory
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILES = [
    str(PROJECT_ROOT / ".env"),
    str(Path(__file__).resolve().parents[2] / ".env"),
    ".env",
]

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://revenuepilot:revenuepilot@localhost:5432/revenuepilot"
    DATABASE_URL_SYNC: str = "postgresql://revenuepilot:revenuepilot@localhost:5432/revenuepilot"
    
    RAZORPAY_KEY_ID: str = "rzp_test_TU75XEFERKd5E2"
    RAZORPAY_KEY_SECRET: str = "XRwXL05CmTbn4am7Wu5jcURR"
    RAZORPAY_WEBHOOK_SECRET: str = ""
    RAZORPAY_MODE: str = "test"
    
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"
    
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "secret"
    
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    
    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()
