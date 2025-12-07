from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.auth.schemas import (UserCreateRequest,
                              UserCreateResponse,
                              LoginRequest,
                              LoginResponse,
                              OauthRequest
                              )
from src.database.setup import get_db_session
from src.auth.service import (create_user,
                              get_user_by_email,
                              get_current_user)


base_router = APIRouter(
    "/auth"
)


@base_router.post("/sign-up",
                  response_model=UserCreateResponse)
async def signup(
    user: UserCreateRequest,
    session=Depends(get_db_session)
):
    response = create_user(
        user,
        session
    )

    return response


@base_router.post("/login",
                  respomse_model=LoginResponse)
def login(
    request: LoginRequest,
    session=Depends(get_db_session)
):
    pass


@base_router.get("/me")
def get_user(
    user=Depends(get_current_user)
):
    return user


@base_router.post("/oauth",
                  response_model=LoginResponse)
def google_auth(
    request: OauthRequest,
    session=Depends(get_db_session)
):
    pass

@base_router.post("forgot-password")
def forgot_password(
    request,
    session=Depends(get_db_session)
):
    pass