from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


UserRole = Literal["user", "admin", "super_admin"]


class UserBaseInput(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = " ".join(value.strip().split())
        if len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters long.")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: EmailStr) -> EmailStr:
        return value


class UserSignupRequest(UserBaseInput):
    confirm_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_password_confirmation(self) -> "UserSignupRequest":
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm password do not match.")
        return self


class PasswordVerificationRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)


class CreateUserRequest(UserBaseInput):
    role: UserRole = "user"


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    role: UserRole = Field(default="user", description="Choose the role you are logging in as.")


class UserPublic(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: UserRole = "user"


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class CreateUserResponse(BaseModel):
    message: str
    user: UserPublic
