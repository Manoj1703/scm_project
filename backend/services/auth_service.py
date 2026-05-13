from fastapi import HTTPException, status

from auth.auth_utils import create_access_token, decode_access_token, hash_password, verify_password


ROLE_LEVELS = {
    "user": 1,
    "admin": 2,
    "super_admin": 3,
}


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


def validate_role(role: str) -> str:
    if role not in ROLE_LEVELS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid role.",
        )
    return role


def has_minimum_role(user_role: str, required_role: str) -> bool:
    return ROLE_LEVELS[user_role] >= ROLE_LEVELS[required_role]
