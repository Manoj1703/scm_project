import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


UserRole = Literal["customer", "user", "admin", "super_admin"]


class UserBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    phone_number: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters long.")
        return cleaned

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = re.sub(r"[\s\-\(\)]", "", value)
        if not re.fullmatch(r"\+?[0-9]{10,15}", cleaned):
            raise ValueError(
                "Phone number must contain 10 to 15 digits and may start with +."
            )
        return cleaned


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    phone_number: str = Field(min_length=7, max_length=20)
    role: Literal["customer"] = "customer"


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(UserBase):
    id: str
    role: UserRole = "customer"


class UserInDB(UserOut):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRoleUpdate(BaseModel):
    role: UserRole


class MessageResponse(BaseModel):
    message: str
