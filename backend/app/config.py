"""Configuration settings for ProductionReady FastAPI orchestrator."""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    PROJECT_NAME: str = "ProductionReady Orchestrator"
    VERSION: str = "0.2.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'productionready.db'}")
    API_KEY: str = os.getenv("PRODUCTIONREADY_API_KEY", "")
    DEFAULT_DEV_KEY: str = "pr_live_dev_test_key_0000"
    REQUIRE_AUTH: bool = os.getenv("REQUIRE_AUTH", "true").lower() in ("true", "1", "yes")
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

    @property
    def effective_api_key(self) -> str:
        """Returns configured API key, falling back to default dev key in non-production."""
        if self.API_KEY:
            return self.API_KEY
        if self.ENVIRONMENT != "production":
            return self.DEFAULT_DEV_KEY
        return ""

settings = Settings()
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
