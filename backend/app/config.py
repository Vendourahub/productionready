"""Configuration settings for ProductionReady FastAPI orchestrator."""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    PROJECT_NAME: str = "ProductionReady Orchestrator"
    VERSION: str = "0.2.0"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'productionready.db'}")
    GITHUB_APP_ID: str = os.getenv("GITHUB_APP_ID", "")
    GITHUB_WEBHOOK_SECRET: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    GITHUB_PRIVATE_KEY_PATH: str = os.getenv("GITHUB_PRIVATE_KEY_PATH", "")
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    REPORTS_DIR: Path = BASE_DIR / "reports"

settings = Settings()
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
