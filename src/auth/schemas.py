from typing import Annotated
from pydantic import BaseModel
from pydantic import EmailStr, StringConstraints
from uuid import UUID


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: Annotated[str, StringConstraints(
        strip_whitespace=True, max_length=64)]
    first_name: str
    last_name: str


class UserCreateResponse(BaseModel):
    msg: str
    access_token: str
    refresh_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    token_type: str = "bearer"
    access_token: str
    refresh_token: str
    is_verified: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str
    token_type: str = "bearer"


class OauthRequest(BaseModel):
    id_token: str


class CurrentUser(BaseModel):
    email: EmailStr
    id: UUID
    is_verified: bool = False
