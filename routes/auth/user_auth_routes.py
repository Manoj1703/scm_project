from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from auth.auth_utils import hash_password
from backend.database.db import get_db
from backend.utils.common import normalize_email, utc_now
from models.auth_models import UserCreate, UserOut


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserOut:
    email = normalize_email(str(payload.email))

    existing_user = await db.users.find_one({"email": email})
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    user_document = {
        "name": payload.name,
        "email": email,
        "hashed_password": hash_password(payload.password),
        "role": "customer",
        "created_at": utc_now(),
        "is_active": True,
    }

    try:
        result = await db.users.insert_one(user_document)
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        ) from exc

    return UserOut(
        id=str(result.inserted_id),
        name=user_document["name"],
        email=user_document["email"],
        role=user_document["role"],
    )
