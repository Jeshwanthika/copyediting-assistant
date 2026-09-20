"""Central configuration. All settings are read from environment variables / .env."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent
DEFAULT_DB_PATH = REPO_DIR / "data" / "copy_editing.db"
SEED_DIR = REPO_DIR / "data" / "seed"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    # Empty string means "use the default SQLite file".
    database_url: str = ""
    # Reserved for the AI stage. Not used yet.
    llm_api_key: str = ""
    cors_origins: str = "http://localhost:3000"

    @property
    def resolved_database_url(self) -> str:
        return self.database_url or f"sqlite:///{DEFAULT_DB_PATH}"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
