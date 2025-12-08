from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import TIMESTAMP, Uuid, inspect
from datetime import datetime
from uuid import UUID

from src.utils import get_current_time, generate_uuid


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    __repr_attrs__ = []
    __repr_max_length__ = 15


class TimeStampedModel(Base):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=get_current_time(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        default=get_current_time,
        index=True
    )

    def set_modified_at(self):
        self.modified_at = get_current_time()
    
    def set_deleted_at(self):
        self.deleted_at = get_current_time()


class RecordModel(TimeStampedModel):
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        index=True,
        default=generate_uuid()
    )

    def __repr__(self) -> str:
        insp = inspect(self)
        if insp.identity is not None:
            id_value = insp.identity[0]
            return f"{self.__class__.__name__}(id={id_value!r})"
        return f"{self.__class__.__name__}(id=None)"
    
    def __hash__(self) -> int:
        self.id.int

    def __eq__(self, _value):
        return isinstance(_value, self.__class__) and self.id == _value.id