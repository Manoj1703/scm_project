from motor.motor_asyncio import AsyncIOMotorDatabase

from auth.access_control import ADMIN_ROLES, Role
from auth.auth_utils import hash_password
from back_end.config import settings
from backend.utils.common import normalize_email, utc_now


async def seed_initial_admin(db: AsyncIOMotorDatabase) -> bool:
    if not (
        settings.INITIAL_SUPER_ADMIN_NAME
        and settings.INITIAL_SUPER_ADMIN_EMAIL
        and settings.INITIAL_SUPER_ADMIN_PASSWORD
    ):
        return False

    existing_admin = await db.users.find_one({"role": {"$in": list(ADMIN_ROLES)}})
    if existing_admin is not None:
        return False

    email = normalize_email(settings.INITIAL_SUPER_ADMIN_EMAIL)
    existing_user = await db.users.find_one({"email": email})
    if existing_user is not None:
        return False

    await db.users.insert_one(
        {
            "name": settings.INITIAL_SUPER_ADMIN_NAME,
            "email": email,
            "hashed_password": hash_password(settings.INITIAL_SUPER_ADMIN_PASSWORD),
            "role": Role.SUPER_ADMIN.value,
            "created_at": utc_now(),
            "is_active": True,
        }
    )
    return True
