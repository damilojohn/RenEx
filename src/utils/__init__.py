from datetime import datetime
from zoneinfo import ZoneInfo
import uuid


def get_current_time() -> datetime:
    return datetime.now(tz=ZoneInfo("Africa/Lagos"))


def generate_uuid() -> uuid.UUID:
    return uuid.uuid4()
