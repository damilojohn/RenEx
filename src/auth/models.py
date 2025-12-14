from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, String

from src.database import RecordModel


class RenExUser(RecordModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320), nullable=False, unique=True, index=True
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean(),
        default=False,
        nullable=True,
        unique=False,
    )

    first_name: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=False,
    )

    last_name: Mapped[str] = mapped_column(String(320), nullable=False, unique=False)

    password_hxh: Mapped[str] = mapped_column(String(320), nullable=False, unique=False)
    listings = relationship("Listings", back_populates="user")

    # Swaps where user is the initiator
    initiated_swaps = relationship(
        "Swap", foreign_keys="Swap.initiator_id", back_populates="initiator"
    )

    # Swaps where user is the recipient
    received_swaps = relationship(
        "Swap", foreign_keys="Swap.recipient_id", back_populates="recipient"
    )
