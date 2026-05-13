import os

import uvicorn
from dotenv import load_dotenv

from main import create_app


load_dotenv()


def _server_host() -> str:
    return os.getenv("APP_HOST", "127.0.0.1")


def _server_port() -> int:
    value = os.getenv("APP_PORT", "8000")
    return int(value)


if __name__ == "__main__":
    uvicorn.run(create_app(), host=_server_host(), port=_server_port(), reload=False)
