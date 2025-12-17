from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from src.config import get_settings
import jwt
from fastapi import HTTPException, status

settings = get_settings()

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=4,
    argon2__memory_cost=65536,
    argon2__parallelism=4,
)


def create_access_token(sub: dict):
    to_encode = sub.copy()
    iat = datetime.now(timezone.utc)
    expire = iat + timedelta(minutes=settings.JWT_EXP)
    to_encode.update({"exp": expire, "iat": iat})
    token = jwt.encode(
        payload=to_encode, key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
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

    payload.update({"exp": to_expire, "iat": iat})

    token = jwt.encode(
        payload=payload,
        key=settings.JWT_REFRESH_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(
            token=token,
            key=settings.JWT_REFRESH_SECRET,
            algorithm=settings.JWT_ALGORITHM,
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
