from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.database.db import get_users_collection
from backend.models.user_model import (
    AuthResponse,
    PasswordVerificationRequest,
    UserLoginRequest,
    UserPublic,
    UserSignupRequest,
)
from backend.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    validate_password_strength,
    verify_password,
)

router = APIRouter(tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _to_public_user(user_document: dict) -> UserPublic:
    return UserPublic(
        id=user_document["id"],
        name=user_document["name"],
        email=user_document["email"],
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserPublic:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    users = get_users_collection()
    user_document = await users.find_one({"id": user_id})

    if user_document is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _to_public_user(user_document)


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserSignupRequest) -> AuthResponse:
    users = get_users_collection()
    email = _normalize_email(str(payload.email))

    validate_password_strength(payload.password)

    existing_user = await users.find_one({"email": email})
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    user_id = str(uuid4())
    now = datetime.now(timezone.utc)
    user_document = {
        "id": user_id,
        "name": payload.name,
        "email": email,
        "password_hash": hash_password(payload.password),
        "created_at": now,
        "updated_at": now,
    }

    await users.insert_one(user_document)

    token = create_access_token({"sub": user_id, "email": email})
    return AuthResponse(access_token=token, user=_to_public_user(user_document))


@router.post("/login", response_model=AuthResponse)
async def login(payload: UserLoginRequest) -> AuthResponse:
    users = get_users_collection()
    email = _normalize_email(str(payload.email))
    user_document = await users.find_one({"email": email})

    if user_document is None or not verify_password(payload.password, user_document["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user_document["id"], "email": user_document["email"]})
    return AuthResponse(access_token=token, user=_to_public_user(user_document))


@router.get("/me", response_model=UserPublic)
async def read_current_user(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
    return current_user


@router.post("/verify-password")
async def verify_current_password(
    payload: PasswordVerificationRequest,
    current_user: UserPublic = Depends(get_current_user),
) -> dict[str, bool]:
    users = get_users_collection()
    user_document = await users.find_one({"id": current_user.id})

    if user_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return {"valid": verify_password(payload.current_password, user_document["password_hash"])}
