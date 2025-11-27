from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager

from src.database.setup import (
    _create_engine,
    create_async_session
)
from src.config import settings, LOG


@asynccontextmanager
async def lifespan(app: FastAPI):
    # set up database connection
    try:
        db_engine = await _create_engine(
            settings.DB_CONNECTION_STRING
        )
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
        db_engine.close()


app = FastAPI(
    title="RenEx Backend Service",
    lifespan=lifespan,
    version="0.1.0"
)

if __name__ == "__main__":
    LOG.info(f"Starting RenEx on host {settings.HOST} on port {settings.PORT}")
    uvicorn.run(
        "app",
        host="0.0.0.0",
        port=8080
    )
