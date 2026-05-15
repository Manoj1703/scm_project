import asyncio
from types import SimpleNamespace

import pytest
from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from models.auth_models import UserCreate
from routes.auth.user_auth_routes import create_user, read_user


class FakeUsersCollection:
    def __init__(self) -> None:
        self.documents: list[dict] = []

    async def find_one(self, query: dict, projection: dict | None = None) -> dict | None:
        if "_id" in query:
            for document in self.documents:
                if document["_id"] == query["_id"]:
                    result = document.copy()
                    if projection and projection.get("password") == 0:
                        result.pop("password", None)
                    return result
            return None

        if "email" in query:
            for document in self.documents:
                if document["email"] == query["email"]:
                    return document
            return None

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


def test_create_user_enforces_email_uniqueness():
    fake_db = FakeDb()
    payload = UserCreate(
        name="Alice Example",
        email="alice@example.com",
        phone_number="+15551234567",
        password="StrongPass123!",
    )

    first = asyncio.run(create_user(payload, db=fake_db))
    assert first.email == "alice@example.com"
    assert first.phone_number == "+15551234567"
    assert first.role == "customer"

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(create_user(payload, db=fake_db))

    assert exc_info.value.status_code == 409


def test_read_user_excludes_password_and_objectid():
    fake_db = FakeDb()
    payload = UserCreate(
        name="Alice Example",
        email="alice@example.com",
        phone_number="+15551234567",
        password="StrongPass123!",
    )
    created = asyncio.run(create_user(payload, db=fake_db))

    result = asyncio.run(read_user(created.id, db=fake_db))

    assert result.id == created.id
    assert result.email == "alice@example.com"
    assert result.name == "Alice Example"
    assert not hasattr(result, "password")
