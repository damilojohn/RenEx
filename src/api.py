from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from src.auth.views import base_router as auth_router


base_router = APIRouter(
    prefix="/renex/api",
    tags=["Heartbeat"]
)


@base_router.post(
    "/heartbeat"
)
def heartbeat():
    """Base endpoint for service. Can be used for app health check

    Args:

    Returns:
        status_code: HTTP Response code
        version: application version

    Raises:
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "RenEx Backend Service",
            "version": "0.1.0",
            "data": {
                "verified": True,
                }
            })


base_router.include_router(auth_router,
                           tags=["Auth"])