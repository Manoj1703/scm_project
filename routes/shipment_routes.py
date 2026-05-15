from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from auth.auth_deps import get_current_user
from backend.database.db import get_db
from backend.utils.common import utc_now
from models.auth_models import UserOut
from models.shipment_model import ShipmentCreate, ShipmentOut, ShipmentStatus


router = APIRouter(prefix="/api/shipments", tags=["shipments"])


def generate_tracking_id() -> str:
    return f"SCM-{uuid4().hex[:8].upper()}"


def _to_shipment_out(document: dict) -> ShipmentOut:
    return ShipmentOut(
        id=str(document["_id"]),
        tracking_id=document["tracking_id"],
        sender=document["sender"],
        receiver=document["receiver"],
        origin=document["origin"],
        destination=document["destination"],
        weight_kg=document["weight_kg"],
        expected_delivery=document["expected_delivery"],
        status=document.get("status", ShipmentStatus.PENDING),
        owner_id=document["owner_id"],
        created_at=document["created_at"],
    )


@router.post("", response_model=ShipmentOut, status_code=status.HTTP_201_CREATED)
async def create_shipment(
    payload: ShipmentCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
) -> ShipmentOut:
    shipment_document = {
        "tracking_id": generate_tracking_id(),
        "sender": payload.sender,
        "receiver": payload.receiver,
        "origin": payload.origin,
        "destination": payload.destination,
        "weight_kg": payload.weight_kg,
        "expected_delivery": payload.expected_delivery,
        "status": ShipmentStatus.PENDING,
        "owner_id": current_user.id,
        "created_at": utc_now(),
    }

    inserted_id = None
    for _ in range(5):
        try:
            result = await db.shipments.insert_one(shipment_document.copy())
            inserted_id = result.inserted_id
            break
        except DuplicateKeyError:
            shipment_document["tracking_id"] = generate_tracking_id()

    if inserted_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate a unique tracking ID.",
        )

    return _to_shipment_out({**shipment_document, "_id": inserted_id})
