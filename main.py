from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

from src.database import Base

from src.database.setup import (
    _create_engine,
    create_async_session
)
from src.config import get_settings, LOG
from src.api import base_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # set up database connection
    try:
        db_engine = await _create_engine(
            settings.DB_CONNECTION_STRING
        )
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_maker = await create_async_session(
            db_engine
        )
        app.state.session_maker = session_maker
    except Exception as e:
        LOG.error(f"Failed to setup DB connection with error {e}")
        raise e
    try:
        LOG.info("RenEx Server Starting....")
        yield
    finally:
        LOG.info("RenEx Server Shutting Down.....")
        await db_engine.dispose()


app = FastAPI(
    title="RenEx Backend Service",
    description="Welcome to RenEx API's Documentation!",
    lifespan=lifespan,
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*","https://ren-ex.vercel.app", "http://localhost:3000"],
    allow_headers=["*"],
    allow_methods=["*"],
    expose_headers=["*"],
    allow_credentials=True
)

app.include_router(base_router)

if __name__ == "__main__":
    LOG.info(f"Starting RenEx on host {settings.HOST} on port {settings.PORT}")
    uvicorn.run(
        "app",
        host="0.0.0.0",
        port=8080
    )
