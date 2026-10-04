import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class Registration(Credentials):
    application_consent: Literal[True]


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=40, max_length=256)


class Tokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    role: Literal["USER", "DERMATOLOGIST", "ADMIN"]
    created_at: datetime


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str = Field(max_length=80)
    language: Literal["fr", "en"] = "fr"


class ProfileRead(ProfileUpdate):
    model_config = ConfigDict(from_attributes=True)
    user_id: uuid.UUID
