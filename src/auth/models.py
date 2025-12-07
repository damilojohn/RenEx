from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, String

from src.database import RecordModel


class RenExUser(RecordModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320),
                                       nullable=False,
                                       unique=True,
                                       index=True)
    email_verified: Mapped[bool] = mapped_column(
        Boolean(),
        default=False,
        nullable=False,
        unique=False,
    )

    first_name: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=False
    )

    password_hxh: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=False
    )
