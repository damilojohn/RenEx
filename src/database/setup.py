from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import (create_async_engine,
                                    AsyncEngine,
                                    async_sessionmaker,
                                    AsyncSession)
from src.config import LOG


async def _create_engine(conn_string: str):
    return create_async_engine(
        url=conn_string,
        connect_args={"ssl": "require"},
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
        pool_pre_ping=True,
    )


async def create_async_session(engine: AsyncEngine):
    return async_sessionmaker(
        autocommit=False,
        autoflush=True,
        bind=engine
    )


async def get_db_session(
        request: Request
) -> AsyncGenerator[AsyncSession]:
    sessionmaker = request.app.state.session_maker
    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            LOG.error(f"db session failed with exception {e}")
            raise e

