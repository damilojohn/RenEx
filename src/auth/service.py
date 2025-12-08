from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from src.config import get_settings
import jwt
from fastapi import HTTPException, status

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

settings = get_settings()

oauth2scheme = OAuth2PasswordBearer(tokenUrl="/auth/form-login")

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=4,
    argon2__memory_cost=65536,
    argon2__parallelism=4,
)


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
                password_hxh=password_hash,
                first_name=user.first_name,
                last_name=user.last_name
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

        if verify_password_hash(
            password=user.password,
            password_hash=db_user.password_hxh
        ):
            access_token = create_access_token({"sub": str(db_user.id)})
            refresh_token = create_refresh_token({"sub": db_user.id})

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


def create_access_token(sub: dict):
    to_encode = sub.copy()
    iat = datetime.now(timezone.utc)
    expire = iat + timedelta(minutes=settings.JWT_EXP)
    to_encode.update({"exp": expire, "iat": iat})
    token = jwt.encode(
        payload=to_encode,
        key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return token


def verify_access_token(token):
    try:
        payload = jwt.decode(token, key=settings.JWT_SECRET_KEY)
        return payload["sub"]
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
        ) from e
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer access token is invalid",
        ) from e


def create_refresh_token(sub: dict):
    payload = sub.copy()

    iat = datetime.now(timezone.utc)
    to_expire = iat + timedelta(days=settings.JWT_REFRESH_EXP)

    payload.update({"exp": to_expire,
                    "iat": iat})

    token = jwt.encode(
        payload=payload,
        key=settings.JWT_REFRESH_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    return token


def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(
            token=token,
            key=settings.JWT_REFRESH_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        return payload["sub"]
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
        ) from e
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer access token is invalid",
        ) from e


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password_hash(password, password_hash) -> str:
    return pwd_context.verify(password, password_hash)


def get_refresh_token(token: str):
    try:
        id = verify_refresh_token(token)
        access_token = create_access_token({"sub": id})
        refresh_token = create_refresh_token({"sub": id})

        return LoginResponse(
            access_token=access_token, refresh_token=refresh_token,
            token_type="bearer"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token credentials"
        ) from e
