from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from auth.auth_deps import get_current_user
from auth.auth_utils import create_access_token, hash_password, verify_password
from backend.database.db import get_db
from backend.utils.common import normalize_email, utc_now
from models.auth_models import Token, UserCreate, UserLogin, UserOut


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


@router.post("/login", response_model=Token)
async def login(
    payload: UserLogin,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Token:
    email = normalize_email(str(payload.email))
    user_document = await db.users.find_one({"email": email})

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user_document is None:
        raise invalid_credentials

    if not verify_password(payload.password, user_document["hashed_password"]):
        raise invalid_credentials

    access_token = create_access_token(
        {
            "sub": str(user_document["_id"]),
            "email": user_document["email"],
            "role": user_document.get("role", "customer"),
        }
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: UserOut = Depends(get_current_user)) -> UserOut:
    return current_user
