import asyncio
from types import SimpleNamespace

import pytest
from bson import ObjectId
from fastapi import HTTPException

from auth.access_control import require_role
from auth.admin_seeder import seed_initial_admin
from models.auth_models import UserOut, UserRoleUpdate
from routes.auth.admin_auth_routes import delete_user, list_users, update_user_role


class FakeCursor:
    def __init__(self, documents: list[dict]) -> None:
        self._documents = documents
        self._index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index >= len(self._documents):
            raise StopAsyncIteration
        document = self._documents[self._index]
        self._index += 1
        return document


class FakeUsersCollection:
    def __init__(self, documents: list[dict] | None = None) -> None:
        self.documents = documents or []

    async def find_one(self, query: dict) -> dict | None:
        if "_id" in query:
            for document in self.documents:
                if document["_id"] == query["_id"]:
                    return document
            return None

        if "email" in query:
            for document in self.documents:
                if document["email"] == query["email"]:
                    return document
            return None

        if "role" in query and isinstance(query["role"], dict):
            roles = set(query["role"].get("$in", []))
            for document in self.documents:
                if document.get("role") in roles:
                    return document
            return None

        return None

    def find(self, query: dict) -> FakeCursor:
        return FakeCursor(self.documents.copy())

    async def update_one(self, query: dict, update: dict) -> SimpleNamespace:
        target_id = query.get("_id")
        for document in self.documents:
            if document["_id"] == target_id:
                document.update(update.get("$set", {}))
                return SimpleNamespace(matched_count=1)
        return SimpleNamespace(matched_count=0)

    async def delete_one(self, query: dict) -> SimpleNamespace:
        target_id = query.get("_id")
        for index, document in enumerate(self.documents):
            if document["_id"] == target_id:
                self.documents.pop(index)
                return SimpleNamespace(deleted_count=1)
        return SimpleNamespace(deleted_count=0)

    async def insert_one(self, document: dict) -> SimpleNamespace:
        stored_document = document.copy()
        stored_document["_id"] = ObjectId()
        self.documents.append(stored_document)
        return SimpleNamespace(inserted_id=stored_document["_id"])


class FakeDb:
    def __init__(self, documents: list[dict] | None = None) -> None:
        self.users = FakeUsersCollection(documents)


def _user(role: str, name: str = "Alice Example", email: str = "alice@example.com") -> UserOut:
    return UserOut(id=str(ObjectId()), name=name, email=email, role=role)


def test_require_role_blocks_customer_access():
    dependency = require_role("admin")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(dependency(current_user=_user("customer")))

    assert exc_info.value.status_code == 403


def test_admin_routes_allow_admin_and_manage_users():
    user_id = ObjectId()
    fake_db = FakeDb(
        [
            {"_id": ObjectId(), "name": "Admin", "email": "admin@example.com", "role": "admin"},
            {"_id": user_id, "name": "Bob Example", "email": "bob@example.com", "role": "customer"},
        ]
    )
    admin_user = _user("admin", name="Admin", email="admin@example.com")

    users = asyncio.run(list_users(db=fake_db, current_user=admin_user))
    assert len(users) == 2
    assert {user.role for user in users} == {"admin", "customer"}

    updated = asyncio.run(
        update_user_role(
            str(user_id),
            UserRoleUpdate(role="admin"),
            db=fake_db,
            current_user=admin_user,
        )
    )
    assert updated.role == "admin"

    deleted = asyncio.run(delete_user(str(user_id), db=fake_db, current_user=admin_user))
    assert deleted.message == "User deleted successfully."
    assert len(fake_db.users.documents) == 1


def test_admin_seeder_is_idempotent():
    fake_db = FakeDb([{"_id": ObjectId(), "name": "Bob", "email": "bob@example.com", "role": "customer"}])

    first_run = asyncio.run(seed_initial_admin(fake_db))
    second_run = asyncio.run(seed_initial_admin(fake_db))

    assert first_run is True
    assert second_run is False
    seeded_admins = [doc for doc in fake_db.users.documents if doc.get("role") == "super_admin"]
    assert len(seeded_admins) == 1
