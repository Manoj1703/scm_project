from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.config import INITIAL_SUPER_ADMIN_EMAIL, INITIAL_SUPER_ADMIN_NAME, INITIAL_SUPER_ADMIN_PASSWORD
from backend.database.db import get_users_collection
from backend.models.user_model import (
    AuthResponse,
    CreateUserRequest,
    CreateUserResponse,
    UserLoginRequest,
    UserPublic,
    UserSignupRequest,
)
from backend.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    validate_role,
    validate_password_strength,
    verify_password,
)
from backend.utils.common import normalize_email, utc_now

router = APIRouter(tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


def _to_public_user(user_document: dict) -> UserPublic:
    return UserPublic(
        id=user_document["id"],
        name=user_document["name"],
        email=user_document["email"],
        role=user_document.get("role", "user"),
    )


def _role_guard(*allowed_roles: str):
    async def dependency(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
        return current_user

    return dependency


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserPublic:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = getattr(request.state, "access_token_payload", None)
    if payload is None:
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


def _build_token_payload(user_document: dict) -> dict[str, str]:
    return {
        "sub": user_document["id"],
        "email": user_document["email"],
        "role": user_document.get("role", "user"),
    }


def _build_user_document(*, name: str, email: str, password: str, role: str) -> dict:
    return {
        "id": str(uuid4()),
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "role": validate_role(role),
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserSignupRequest) -> AuthResponse:
    users = get_users_collection()
    email = normalize_email(str(payload.email))

    validate_password_strength(payload.password)

    existing_user = await users.find_one({"email": email})
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    user_document = _build_user_document(
        name=payload.name,
        email=email,
        password=payload.password,
        role="user",
    )

    await users.insert_one(user_document)

    token = create_access_token(_build_token_payload(user_document))
    return AuthResponse(
        access_token=token,
        user=_to_public_user(user_document),
    )


@router.post("/login", response_model=AuthResponse)
async def login(payload: UserLoginRequest) -> AuthResponse:
    users = get_users_collection()
    email = normalize_email(str(payload.email))
    user_document = await users.find_one({"email": email})

    if user_document is None or not verify_password(payload.password, user_document["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stored_role = user_document.get("role", "user")
    if payload.role != stored_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This account is registered as {stored_role.replace('_', ' ')}.",
        )

    token = create_access_token(_build_token_payload(user_document))
    return AuthResponse(
        access_token=token,
        user=_to_public_user(user_document),
    )


@router.get("/me", response_model=UserPublic)
async def read_current_user(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
    return current_user


@router.get("/admin/me", response_model=UserPublic)
async def read_admin_profile(current_user: UserPublic = Depends(_role_guard("admin", "super_admin"))) -> UserPublic:
    return current_user


@router.get("/super-admin/me", response_model=UserPublic)
async def read_super_admin_profile(
    current_user: UserPublic = Depends(_role_guard("super_admin")),
) -> UserPublic:
    return current_user


@router.post("/admin/users", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_by_admin(
    payload: CreateUserRequest,
    current_user: UserPublic = Depends(_role_guard("super_admin")),
) -> CreateUserResponse:
    users = get_users_collection()
    email = normalize_email(str(payload.email))

    validate_password_strength(payload.password)
    validate_role(payload.role)

    existing_user = await users.find_one({"email": email})
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    user_document = _build_user_document(
        name=payload.name,
        email=email,
        password=payload.password,
        role=payload.role,
    )

    await users.insert_one(user_document)
    return CreateUserResponse(
        message=f"{payload.role.replace('_', ' ').title()} account created successfully.",
        user=_to_public_user(user_document),
    )


async def ensure_initial_super_admin() -> bool:
    if not (INITIAL_SUPER_ADMIN_NAME and INITIAL_SUPER_ADMIN_EMAIL and INITIAL_SUPER_ADMIN_PASSWORD):
        return False

    users = get_users_collection()
    email = normalize_email(INITIAL_SUPER_ADMIN_EMAIL)
    existing_user = await users.find_one({"email": email})
    if existing_user is not None:
        return False

    user_document = _build_user_document(
        name=INITIAL_SUPER_ADMIN_NAME,
        email=email,
        password=INITIAL_SUPER_ADMIN_PASSWORD,
        role="super_admin",
    )
    await users.insert_one(user_document)
    return True
