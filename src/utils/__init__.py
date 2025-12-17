import json
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


class CustomJSONEncoder(json.JSONEncoder):

    def encode(self, obj):
        """Writing a custom serializer to handle UUIDs and other types"""

        def serialize_datetime(o):
            if isinstance(o, datetime):
                return o.isoformat()
            elif hasattr(o, "isoformat"):
                return o.isoformat()
            elif isinstance(o, dict):
                return {k: serialize_datetime(v) for k,v in o.items()}
            elif isinstance(o, list):
                return [serialize_datetime(item) for item in o]
            return o

        def serialize_uuid(o):
            if isinstance(o, uuid.UUID):
                return str(o)
            elif isinstance(o, list):
                return [serialize_uuid(item) for item in obj]

            elif isinstance(o, dict):
                return {k: serialize_uuid(v) for k, v in o.items()}
            else:
                return o

        obj = serialize_uuid(obj)
        obj = serialize_datetime(obj)

        return super().encode(obj)


class CustomJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            cls=CustomJSONEncoder
        ).encode("utf-8")
