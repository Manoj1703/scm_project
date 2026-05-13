import uvicorn

from backend.config import APP_HOST, APP_PORT
from main import create_app


if __name__ == "__main__":
    uvicorn.run(create_app(), host=APP_HOST, port=APP_PORT, reload=False, log_config=None)
