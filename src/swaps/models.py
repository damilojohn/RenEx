from src.database import RecordModel
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, TIMESTAMP, Float, ForeignKey, Text
from datetime import datetime, timezone
from uuid import UUID
from src.swaps.enums import SwapStatus


class Swap(RecordModel):
    __tablename__ = "swaps"

    # The listing that this swap is based on
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("listings.id", ondelete="cascade"), nullable=False, index=True
    )

    # User who initiated the swap (the one making the request)
    initiator_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="cascade"), nullable=False, index=True
    )

    # User who owns the listing (the recipient of the swap request)
    recipient_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="cascade"), nullable=False, index=True
    )

    # Swap details
    proposed_volume: Mapped[float] = mapped_column(
        Float(), nullable=False
    )  # Volume the initiator wants to swap

    proposed_price: Mapped[float] = mapped_column(
        Float(), nullable=True
    )  # Optional negotiated price

    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=SwapStatus.PENDING.value, index=True
    )

    message: Mapped[str] = mapped_column(
        Text(), nullable=True
    )  # Optional message from initiator

    # Timestamps for swap lifecycle
    proposed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    responded_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )  # When recipient accepted/rejected

    completed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )  # When swap was completed

    # Relationships
    listing = relationship("Listings", back_populates="swaps")

    initiator = relationship(
        "RenExUser", foreign_keys=[initiator_id], back_populates="initiated_swaps"
    )

    recipient = relationship(
        "RenExUser", foreign_keys=[recipient_id], back_populates="received_swaps"
    )
