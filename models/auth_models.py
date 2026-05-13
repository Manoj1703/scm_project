from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


UserRole = Literal["customer", "user", "admin", "super_admin"]


class UserBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=50)
    email: EmailStr

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters long.")
        return cleaned


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    role: Literal["customer"] = "customer"


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(UserBase):
    id: str
    role: Literal["customer"] = "customer"


class UserInDB(UserOut):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
