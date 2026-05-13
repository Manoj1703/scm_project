import asyncio
from datetime import timedelta
from types import SimpleNamespace

import pytest
from bson import ObjectId
from fastapi import HTTPException
from jose import jwt

from auth.auth_config import JWT_ALGORITHM, JWT_SECRET
from auth.auth_utils import create_access_token, hash_password
from models.auth_models import UserLogin
from routes.auth.user_auth_routes import login


class FakeUsersCollection:
    def __init__(self, documents: list[dict]) -> None:
        self.documents = documents

    async def find_one(self, query: dict) -> dict | None:
        email = query.get("email")
        for document in self.documents:
            if document["email"] == email:
                return document
        return None


class FakeDb:
    def __init__(self, documents: list[dict]) -> None:
        self.users = FakeUsersCollection(documents)


def test_create_access_token_encodes_expected_claims():
    token = create_access_token(
        {"sub": "user-123", "email": "alice@example.com", "role": "customer"},
        expires=timedelta(minutes=30),
    )

    claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

    assert claims["sub"] == "user-123"
    assert claims["email"] == "alice@example.com"
    assert claims["role"] == "customer"
    assert claims["type"] == "access"
    assert "exp" in claims


def test_login_returns_token_and_rejects_invalid_credentials_with_same_message():
    user_document = {
        "_id": ObjectId(),
        "email": "alice@example.com",
        "hashed_password": hash_password("StrongPass123!"),
        "role": "customer",
    }
    fake_db = FakeDb([user_document])

    token = asyncio.run(
        login(UserLogin(email="alice@example.com", password="StrongPass123!"), fake_db)
    )
    assert token.token_type == "bearer"
    assert token.access_token

    wrong_email_error = None
    try:
        asyncio.run(login(UserLogin(email="wrong@example.com", password="StrongPass123!"), fake_db))
    except HTTPException as exc:
        wrong_email_error = exc

    wrong_password_error = None
    try:
        asyncio.run(login(UserLogin(email="alice@example.com", password="WrongPass123!"), fake_db))
    except HTTPException as exc:
        wrong_password_error = exc

    assert wrong_email_error is not None
    assert wrong_password_error is not None
    assert wrong_email_error.status_code == 401
    assert wrong_password_error.status_code == 401
    assert wrong_email_error.detail == wrong_password_error.detail == "Invalid email or password."
