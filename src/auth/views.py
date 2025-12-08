from typing import Annotated
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.schemas import (UserCreateRequest,
                              UserCreateResponse,
                              LoginRequest,
                              LoginResponse,
                              OauthRequest,
                              RefreshRequest
                              )
from src.database.setup import get_db_session
from src.auth.service import (create_user,
                              authenticate_user,
                              get_current_user,
                              get_refresh_token)


base_router = APIRouter(
    prefix="/auth"
)


@base_router.post("/sign-up",
                  response_model=UserCreateResponse)
async def signup(
    user: UserCreateRequest,
    session=Depends(get_db_session)
):
    response = await create_user(
        user,
        session
    )
    if response:
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            detail=response.model_dump()
        )


@base_router.post("/login",
                  response_model=LoginResponse)
async def login(
    user: LoginRequest,
    session=Depends(get_db_session)
):
    try:
        resp = await authenticate_user(
            user,
            session
        )
    except Exception as e:
        raise e
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=resp.model_dump()

    )


@base_router.get("/me")
def get_user(
    user=Depends(get_current_user)
):
    return user


@base_router.post("/form-login")
async def form_login(
    data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session=Depends(get_db_session)
):
    try:
        user = LoginRequest(
            email=data.username,
            password=data.password
        )
        resp = await authenticate_user(
            user,
            session
        )
    except Exception as e:
        raise e
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=resp.model_dump()
    )

@base_router.post("/refresh-token",
                  response_model=LoginResponse)
def get_verify_refresh_token(
    request: RefreshRequest,
    session=Depends(get_db_session)
):
    try:

        resp = get_refresh_token(request.refresh_token)
        if resp:
            return JSONResponse(
                content=resp.model_dump(),
                status_code=status.HTTP_201_CREATED
            )
    except Exception as e:
        raise e


@base_router.post("/google-oauth",
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
