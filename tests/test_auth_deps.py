import asyncio
from datetime import timedelta
from types import SimpleNamespace

import pytest
from bson import ObjectId
from fastapi import HTTPException

from auth.auth_deps import get_current_user, oauth2_scheme
from auth.auth_utils import create_access_token
from main import create_app


class FakeUsersCollection:
    def __init__(self, documents: list[dict]) -> None:
        self.documents = documents

    async def find_one(self, query: dict) -> dict | None:
        user_id = query.get("_id")
        for document in self.documents:
            if document["_id"] == user_id:
                return document
        return None


class FakeDb:
    def __init__(self, documents: list[dict]) -> None:
        self.users = FakeUsersCollection(documents)


def test_get_current_user_returns_user_for_valid_token():
    user_id = ObjectId()
    fake_db = FakeDb(
        [
            {
                "_id": user_id,
                "name": "Alice Example",
                "email": "alice@example.com",
                "role": "customer",
            }
        ]
    )
    token = create_access_token(
        {"sub": str(user_id), "email": "alice@example.com", "role": "customer"},
        expires=timedelta(minutes=30),
    )

    user = asyncio.run(get_current_user(token=token, db=fake_db))

    assert user.id == str(user_id)
    assert user.email == "alice@example.com"
    assert user.role == "customer"


def test_get_current_user_rejects_missing_header():
    fake_db = FakeDb([])

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(token=None, db=fake_db))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated."


def test_get_current_user_rejects_tampered_token():
    fake_db = FakeDb([])

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(token="tampered.token.value", db=fake_db))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token."


def test_get_current_user_rejects_expired_token():
    user_id = ObjectId()
    fake_db = FakeDb(
        [
            {
                "_id": user_id,
                "name": "Alice Example",
                "email": "alice@example.com",
                "role": "customer",
            }
        ]
    )
    expired_token = create_access_token(
        {"sub": str(user_id), "email": "alice@example.com", "role": "customer"},
        expires=timedelta(seconds=-1),
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(token=expired_token, db=fake_db))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token has expired."


def test_openapi_registers_oauth2_security_scheme():
    app = create_app()
    schema = app.openapi()

    assert "/api/auth/me" in schema["paths"]
    assert "OAuth2PasswordBearer" in schema["components"]["securitySchemes"]
    assert schema["components"]["securitySchemes"]["OAuth2PasswordBearer"]["flows"]["password"][
        "tokenUrl"
    ] == "/api/auth/login"
