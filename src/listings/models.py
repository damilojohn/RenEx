from src.database import RecordModel
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, TIMESTAMP, Float, ForeignKey
from datetime import datetime
from uuid import UUID


class ListingStatus(str):
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Listings(RecordModel):
    __tablename__ = "listings"

    listing_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # "demand" or "supply"

    energy_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # "solar" or "wind"

    volume: Mapped[float] = mapped_column(Float(), nullable=False)

    price: Mapped[float] = mapped_column(Float(), nullable=False)

    location: Mapped[str] = mapped_column(
        String(500), nullable=False
    )  # Location of the farm/energy source

    start_time: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, index=True
    )

    end_time: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, index=True
    )

    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active", index=True
    )  # active, inactive, completed, cancelled

    description: Mapped[str] = mapped_column(String(1000), nullable=True)

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="cascade"), nullable=False, index=True
    )

    # Relationship to user
    user = relationship("RenExUser", back_populates="listings")
    # Relationship to swaps
    swaps = relationship("Swap", back_populates="listing", cascade="all, delete-orphan")
