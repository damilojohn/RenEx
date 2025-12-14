from datetime import datetime
from zoneinfo import ZoneInfo
import uuid
from fastapi.responses import JSONResponse
from typing import Any


def get_current_time() -> datetime:
    return datetime.now(tz=ZoneInfo("Africa/Lagos"))


def generate_uuid() -> uuid.UUID:
    return uuid.uuid4()


def send_json_response(content: Any, status: int) -> JSONResponse:
    return JSONResponse(content=content, status=status)
