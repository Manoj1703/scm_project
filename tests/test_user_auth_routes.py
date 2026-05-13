import asyncio
from types import SimpleNamespace

import pytest
from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from models.auth_models import UserCreate
from routes.auth.user_auth_routes import signup


class FakeUsersCollection:
    def __init__(self) -> None:
        self.documents = []

    async def find_one(self, query: dict) -> dict | None:
        email = query.get("email")
        for document in self.documents:
            if document["email"] == email:
                return document
        return None

    async def insert_one(self, document: dict) -> SimpleNamespace:
        if any(existing["email"] == document["email"] for existing in self.documents):
            raise DuplicateKeyError("duplicate key")

        stored_document = document.copy()
        stored_document["_id"] = ObjectId()
        self.documents.append(stored_document)
        return SimpleNamespace(inserted_id=stored_document["_id"])


class FakeDb:
    def __init__(self) -> None:
        self.users = FakeUsersCollection()


def test_signup_creates_customer_user_and_excludes_password():
    fake_db = FakeDb()
    payload = UserCreate(name="Alice Example", email="alice@example.com", password="StrongPass123!")

    result = asyncio.run(signup(payload, fake_db))

    assert result.email == "alice@example.com"
    assert result.name == "Alice Example"
    assert result.role == "customer"
    assert not hasattr(result, "hashed_password")
    assert fake_db.users.documents[0]["is_active"] is True
    assert fake_db.users.documents[0]["role"] == "customer"
    assert "hashed_password" in fake_db.users.documents[0]


def test_signup_duplicate_email_returns_409():
    fake_db = FakeDb()
    payload = UserCreate(name="Alice Example", email="alice@example.com", password="StrongPass123!")

    asyncio.run(signup(payload, fake_db))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(signup(payload, fake_db))

    assert exc_info.value.status_code == 409
