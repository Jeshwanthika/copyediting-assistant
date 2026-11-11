"""Central configuration. All settings are read from environment variables / .env."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent
DATA_DIR = REPO_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "copy_editing.db"
SEED_DIR = DATA_DIR / "seed"
DEFAULT_DOCUMENTS_DIR = DATA_DIR / "documents"
SECRET_FILE = DATA_DIR / ".auth_secret"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    # Empty string means "use the default SQLite file".
    database_url: str = ""
    # Reserved for the AI stage. Not used yet.
    llm_api_key: str = ""
    cors_origins: str = "http://localhost:3000"

    # --- Login -------------------------------------------------------------
    # Key used to sign login tokens. Leave empty to have one generated and kept in
    # data/.auth_secret. Changing it signs everybody out.
    auth_secret_key: str = ""
    # How long a login lasts before the user has to sign in again.
    auth_token_hours: int = 12
    # Accounts created automatically the first time the backend starts with no users.
    # CHANGE THESE PASSWORDS (here or with `python -m app.users set-password`).
    default_lead_username: str = "lead"
    default_lead_password: str = "lead12345"
    default_trainee_username: str = "trainee"
    default_trainee_password: str = "trainee12345"

    # --- Errors & solutions PDFs ---------------------------------------------
    # Leave empty to store uploaded PDFs in data/documents/.
    documents_dir: str = ""
    max_document_mb: int = 25

    @property
    def resolved_database_url(self) -> str:
        return self.database_url or f"sqlite:///{DEFAULT_DB_PATH}"

    @property
    def resolved_documents_dir(self) -> Path:
        return Path(self.documents_dir) if self.documents_dir else DEFAULT_DOCUMENTS_DIR

    @property
    def resolved_secret_key(self) -> str:
        """The configured key, or a random one generated once and kept in data/.auth_secret."""
        if self.auth_secret_key:
            return self.auth_secret_key
        if SECRET_FILE.exists():
            return SECRET_FILE.read_text(encoding="utf-8").strip()
        import secrets

        SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
        key = secrets.token_urlsafe(48)
        SECRET_FILE.write_text(key, encoding="utf-8")
        return key

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
