from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi import HTTPException, status

from backend.config import ACCESS_TOKEN_EXPIRE_DAYS, JWT_ALGORITHM, JWT_SECRET_KEY


def validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long.",
        )

    if len(password) > 128:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be 128 characters or fewer.",
        )

    if " " in password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password cannot contain spaces.",
        )

    if not any(char.islower() for char in password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one lowercase letter.",
        )

    if not any(char.isupper() for char in password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one uppercase letter.",
        )

    if not any(char.isdigit() for char in password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one number.",
        )

    if not any(not char.isalnum() for char in password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one special character.",
        )


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(payload: dict[str, Any]) -> str:
    token_payload = payload.copy()
    expires_at = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    token_payload.update(
        {
            "exp": expires_at,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }
    )
    return jwt.encode(token_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if decoded.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return decoded
