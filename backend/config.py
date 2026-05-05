import os

from dotenv import load_dotenv


load_dotenv()


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set.")
    return value


APP_HOST = required_env("APP_HOST")
APP_PORT = int(required_env("APP_PORT"))
MONGODB_URI = required_env("MONGODB_URI")
MONGODB_DB_NAME = required_env("MONGODB_DB_NAME")
JWT_SECRET_KEY = required_env("JWT_SECRET_KEY")
JWT_ALGORITHM = required_env("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_DAYS = int(required_env("ACCESS_TOKEN_EXPIRE_DAYS"))
