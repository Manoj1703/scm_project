# SCMXPertLite

SCMXPertLite is a lightweight enterprise learning project for practicing source control management, backend architecture, and clean repository habits.

## Current Stack

- Python 3.11+
- FastAPI for the backend API layer
- MongoDB with Motor/PyMongo for persistence
- JWT for authentication
- bcrypt for password hashing
- python-dotenv for environment-based configuration
- Kafka-ready dependency for event-driven extension work
- Frontend HTML/CSS/JavaScript for the client side

## Repository Layout

- `main.py` - FastAPI application entry point
- `run.py` - programmatic Uvicorn launcher
- `backend/` - API, services, database, middleware, and model code
- `frontend/` - static client files
- `requirements.txt` - Python dependencies
- `docs/` - architecture and project overview notes

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Create a local `.env` file with the required runtime values.
4. Run the API with `python run.py`.

## Repo Hygiene

- Keep secrets in `.env` only, never commit it.
- Keep `.venv/`, `venv/`, `__pycache__/`, and generated files out of git.
- Use `main` for stable code, `dev` for integration, and feature branches for isolated work.

## Docs

- [Architecture diagram and system notes](docs/architecture.md)
- [SCMXPertLite overview and tech choices](docs/scmxpertlite-overview.md)
