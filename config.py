"""Application configuration."""
from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database (PostgreSQL)
    database_url: str = "postgresql+psycopg2://afid_user:afid_pass@localhost:5432/afid_hms_db"
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production-at-least-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Server
    debug: bool = True
    log_level: str = "INFO"
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"
    
    # API
    api_title: str = "AFID Orthodontic HMS API"
    api_version: str = "1.0.0"
    api_description: str = "Unified backend for AFID Orthodontic Hospital Management System"
    
    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        """Normalize the DB URL to the psycopg2 driver.

        Managed platforms (Railway, Render, Heroku) hand out `postgres://…` or
        `postgresql://…`; SQLAlchemy needs an explicit driver, so upgrade both to
        `postgresql+psycopg2://…`. Anything else (e.g. an already-qualified URL)
        is left untouched.
        """
        if value.startswith("postgres://"):
            return "postgresql+psycopg2://" + value[len("postgres://"):]
        if value.startswith("postgresql://"):
            return "postgresql+psycopg2://" + value[len("postgresql://"):]
        return value

    @property
    def allowed_origins_list(self) -> List[str]:
        """Comma-separated origins → list, with any trailing slash removed so the
        value matches the browser's `Origin` header exactly."""
        return [
            origin.strip().rstrip("/")
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
