from sqlalchemy import select
from fastapi import status, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from src.auth.models import RenExUser
from src.database.setup import AsyncSession, get_db_session
from src.auth.schemas import (
    UserCreateRequest,
    UserCreateResponse,
    LoginRequest,
    LoginResponse,
    CurrentUser
)

from src.auth.utils import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    get_password_hash,
    verify_password_hash
)

oauth2scheme = OAuth2PasswordBearer(tokenUrl="/auth/form-login")


async def get_user_by_email(
        email: str,
        session: AsyncSession
):
    result = await session.execute(
        select(RenExUser).filter(
            RenExUser.email == email
        )
    )
    user = result.scalar_one_or_none()
    return user


async def create_user(user: UserCreateRequest,
                      session: AsyncSession):
    # check if user exists
    try:
        db_user = await get_user_by_email(
            user.email,
            session
        )

        if db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User with email already exists"
            )
        else:
            password_hash = get_password_hash(user.password)
            new_user = RenExUser(
                email=user.email,
                password_hxh=password_hash
            )

            session.add(new_user)
            await session.commit()

            await session.refresh(db_user)

            access_token = create_access_token({"sub": str(new_user.id)})
            refresh_token = create_refresh_token({"sub": str(new_user.id)})

            return UserCreateResponse(
                msg="Created User Successfully",
                access_token=access_token,
                refresh_token=refresh_token
            )

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed creating new user with error {e}"
        )


async def authenticate_user(
        user: LoginRequest,
        session: AsyncSession
):
    db_user = await get_user_by_email(
        user.email,
        session
    )
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User doesn't exist"
        )
    else:
        password_hash = get_password_hash(user.password)

        if verify_password_hash(
            user_pass=password_hash,
            db_pass=db_user.password_hxh
        ):
            access_token = create_access_token(db_user)
            refresh_token = create_refresh_token(db_user)

            return LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token
            )
        else:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials provided"
            )


async def get_current_user(
        token=Depends(oauth2scheme),
        session: AsyncSession = Depends(get_db_session)
) -> CurrentUser:
    """Get current user from bearer token"""

    try:
        user_id = verify_access_token(token)

        result = await session.execute(
            select(RenExUser).filter(
                RenExUser.id == user_id
            )
        )
        user = result.scalar_one_or_none()

        if user:
            user_resp = CurrentUser(
                email=user.email,
                is_verified=user.email_verified
            )
            return user_resp

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token"
        ) from e
    
