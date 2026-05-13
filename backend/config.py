import os

from dotenv import load_dotenv


load_dotenv()


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set.")
    return value


def optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    return value.strip()


def csv_env(name: str) -> list[str]:
    raw_value = os.getenv(name)
    if not raw_value:
        raise RuntimeError(f"{name} is not set.")

    values = [item.strip() for item in raw_value.split(",")]
    return [item for item in values if item]


APP_TITLE = required_env("APP_TITLE")
APP_VERSION = required_env("APP_VERSION")
APP_DESCRIPTION = required_env("APP_DESCRIPTION")
APP_HOST = required_env("APP_HOST")
APP_PORT = int(required_env("APP_PORT"))
INITIAL_SUPER_ADMIN_NAME = optional_env("INITIAL_SUPER_ADMIN_NAME")
INITIAL_SUPER_ADMIN_EMAIL = optional_env("INITIAL_SUPER_ADMIN_EMAIL")
INITIAL_SUPER_ADMIN_PASSWORD = optional_env("INITIAL_SUPER_ADMIN_PASSWORD")
MONGODB_URI = required_env("MONGODB_URI")
MONGODB_DB_NAME = required_env("MONGODB_DB_NAME")
JWT_SECRET_KEY = required_env("JWT_SECRET_KEY")
JWT_ALGORITHM = required_env("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_DAYS = int(required_env("ACCESS_TOKEN_EXPIRE_DAYS"))
CORS_ORIGINS = csv_env("CORS_ORIGINS")
