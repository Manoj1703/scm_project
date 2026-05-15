import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from bson import ObjectId
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError

from back_end.db.database import ensure_indexes
from models.auth_models import UserOut
from models.shipment_model import ShipmentCreate, ShipmentStatus
from routes.shipment_routes import create_shipment


class FakeUsersCollection:
    def __init__(self) -> None:
        self.indexes = {"id_1": {"key": [("id", 1)]}}
        self.dropped_indexes: list[str] = []
        self.created_indexes: list[tuple[str, bool]] = []

    async def index_information(self) -> dict:
        return self.indexes

    async def drop_index(self, name: str) -> None:
        self.dropped_indexes.append(name)
        self.indexes.pop(name, None)

    async def create_index(self, field: str, unique: bool = False) -> str:
        self.created_indexes.append((field, unique))
        self.indexes[f"{field}_1"] = {"unique": unique}
        return f"{field}_1"


class FakeShipmentsCollection:
    def __init__(self) -> None:
        self.documents: list[dict] = []
        self.created_indexes: list[tuple[str, bool]] = []

    async def insert_one(self, document: dict) -> SimpleNamespace:
        if any(existing["tracking_id"] == document["tracking_id"] for existing in self.documents):
            raise DuplicateKeyError("duplicate tracking_id")

        stored_document = document.copy()
        stored_document["_id"] = ObjectId()
        self.documents.append(stored_document)
        return SimpleNamespace(inserted_id=stored_document["_id"])

    async def create_index(self, field: str, unique: bool = False) -> str:
        self.created_indexes.append((field, unique))
        return f"{field}_1"


class FakeDb:
    def __init__(self) -> None:
        self.users = FakeUsersCollection()
        self.shipments = FakeShipmentsCollection()


def _user(role: str = "customer") -> UserOut:
    return UserOut(
        id=str(ObjectId()),
        name="Alice Example",
        email="alice@example.com",
        role=role,
    )


def test_shipment_create_rejects_spoofed_server_fields():
    with pytest.raises(ValidationError):
        ShipmentCreate.model_validate(
            {
                "sender": "Alice Example",
                "receiver": "Bob Example",
                "origin": "Boston",
                "destination": "Dallas",
                "weight_kg": 2.5,
                "expected_delivery": datetime.now(timezone.utc),
                "tracking_id": "SCM-12345678",
                "status": "DELIVERED",
                "owner_id": "spoofed-owner",
            }
        )


def test_create_shipment_sets_owner_status_and_tracking_id(monkeypatch):
    fake_db = FakeDb()
    current_user = _user()
    tracking_ids = iter(["SCM-AAAA1111", "SCM-BBBB2222"])
    monkeypatch.setattr("routes.shipment_routes.generate_tracking_id", lambda: next(tracking_ids))

    payload = ShipmentCreate(
        sender="Alice Example",
        receiver="Bob Example",
        origin="Boston",
        destination="Dallas",
        weight_kg=2.5,
        expected_delivery=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
    )

    first = asyncio.run(create_shipment(payload, db=fake_db, current_user=current_user))
    second = asyncio.run(create_shipment(payload, db=fake_db, current_user=current_user))

    assert first.tracking_id == "SCM-AAAA1111"
    assert second.tracking_id == "SCM-BBBB2222"
    assert first.tracking_id != second.tracking_id
    assert first.status == ShipmentStatus.PENDING
    assert second.status == ShipmentStatus.PENDING
    assert first.owner_id == current_user.id
    assert second.owner_id == current_user.id
    assert fake_db.shipments.documents[0]["status"] == ShipmentStatus.PENDING
    assert fake_db.shipments.documents[0]["owner_id"] == current_user.id


def test_ensure_indexes_creates_unique_tracking_id_index():
    fake_db = FakeDb()

    asyncio.run(ensure_indexes(fake_db))

    assert fake_db.users.dropped_indexes == ["id_1"]
    assert ("email", True) in fake_db.users.created_indexes
    assert ("tracking_id", True) in fake_db.shipments.created_indexes
