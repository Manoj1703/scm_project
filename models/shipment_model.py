from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ShipmentStatus(str, Enum):
    PENDING = "PENDING"
    IN_TRANSIT = "IN_TRANSIT"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class ShipmentBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    sender: str = Field(min_length=2, max_length=100)
    receiver: str = Field(min_length=2, max_length=100)
    origin: str = Field(min_length=2, max_length=100)
    destination: str = Field(min_length=2, max_length=100)
    weight_kg: float = Field(gt=0)
    expected_delivery: datetime


class ShipmentCreate(ShipmentBase):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ShipmentInDB(ShipmentBase):
    tracking_id: str
    status: ShipmentStatus = ShipmentStatus.PENDING
    owner_id: str
    created_at: datetime


class ShipmentOut(ShipmentInDB):
    id: str
