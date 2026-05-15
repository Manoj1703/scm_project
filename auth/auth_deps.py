from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from auth.auth_utils import decode_access_token
from backend.database.db import get_db
from models.auth_models import DEFAULT_USER_ROLE, UserOut


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserOut:
    if not token:
        raise _unauthorized("Not authenticated.")

    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise _unauthorized("Invalid token payload.")

    try:
        object_id = ObjectId(user_id)
    except Exception as exc:
        raise _unauthorized("Invalid token payload.") from exc

    user_document = await db.users.find_one({"_id": object_id})
    if user_document is None:
        raise _unauthorized("User not found.")

    return UserOut(
        id=str(user_document["_id"]),
        name=user_document["name"],
        email=user_document["email"],
        phone_number=user_document.get("phone_number"),
        role=user_document.get("role", DEFAULT_USER_ROLE),
    )
