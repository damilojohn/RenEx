from typing import Annotated
from pydantic import BaseModel
from pydantic import EmailStr, StringConstraints
from uuid import UUID


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: Annotated[str, StringConstraints(
        strip_whitespace=True, max_length=64)]


class UserCreateResponse(BaseModel):
    msg: str
    access_token: str
    refresh_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    is_verified: bool


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str


class OauthRequest(BaseModel):
    id_token: str


class CurrentUser(BaseModel):
    email: EmailStr
    id: UUID
    is_verified: bool
