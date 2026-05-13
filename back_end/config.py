from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_TITLE: str = "SCMXPertLite API"
    APP_VERSION: str = "0.3.0"
    APP_DESCRIPTION: str = "Backend API for SCMXPertLite."
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    MONGO_URL: str
    DB_NAME: str
    JWT_SECRET: str
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(default_factory=list)
    INITIAL_SUPER_ADMIN_NAME: str | None = None
    INITIAL_SUPER_ADMIN_EMAIL: str | None = None
    INITIAL_SUPER_ADMIN_PASSWORD: str | None = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        raise TypeError("CORS_ORIGINS must be a string or list.")


settings = Settings()
