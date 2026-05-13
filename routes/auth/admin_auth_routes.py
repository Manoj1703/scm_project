from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from auth.access_control import require_role
from backend.database.db import get_db
from models.auth_models import MessageResponse, UserOut, UserRoleUpdate


router = APIRouter(prefix="/api/admin", tags=["admin"])


def _to_user_out(user_document: dict) -> UserOut:
    return UserOut(
        id=str(user_document["_id"]),
        name=user_document["name"],
        email=user_document["email"],
        role=user_document.get("role", "customer"),
    )


def _parse_object_id(user_id: str) -> ObjectId:
    try:
        return ObjectId(user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        ) from exc


@router.get("/users", response_model=list[UserOut])
async def list_users(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(require_role("admin")),
) -> list[UserOut]:
    users: list[UserOut] = []
    async for document in db.users.find({}):
        users.append(_to_user_out(document))
    return users


@router.patch("/users/{user_id}/role", response_model=UserOut)
async def update_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(require_role("admin")),
) -> UserOut:
    object_id = _parse_object_id(user_id)
    result = await db.users.update_one({"_id": object_id}, {"$set": {"role": payload.role}})
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user_document = await db.users.find_one({"_id": object_id})
    if user_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return _to_user_out(user_document)


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(require_role("admin")),
) -> MessageResponse:
    object_id = _parse_object_id(user_id)
    result = await db.users.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return MessageResponse(message="User deleted successfully.")
