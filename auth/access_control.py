from enum import Enum

from fastapi import Depends, HTTPException, status

from auth.auth_deps import get_current_user
from models.auth_models import UserOut


class Role(str, Enum):
    CUSTOMER = "customer"
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


ROLE_RANKS: dict[Role, int] = {
    Role.CUSTOMER: 0,
    Role.USER: 1,
    Role.ADMIN: 2,
    Role.SUPER_ADMIN: 3,
}

ADMIN_ROLES = frozenset({Role.ADMIN.value, Role.SUPER_ADMIN.value})


def require_role(required_role: str):
    required = Role(required_role)

    async def dependency(current_user: UserOut = Depends(get_current_user)) -> UserOut:
        try:
            current_role = Role(current_user.role)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            ) from exc

        if ROLE_RANKS[current_role] < ROLE_RANKS[required]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
        return current_user

    return dependency
