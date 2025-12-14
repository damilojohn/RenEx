from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from src.swaps.enums import SwapStatus


class SwapCreateRequest(BaseModel):
    listing_id: UUID = Field(..., description="ID of the listing to swap with")
    proposed_volume: float = Field(
        ..., gt=0, description="Volume of energy to swap in kWh"
    )
    proposed_price: Optional[float] = Field(
        None, gt=0, description="Optional negotiated price per kWh"
    )
    message: Optional[str] = Field(
        None, max_length=1000, description="Optional message to the listing owner"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "listing_id": "123e4567-e89b-12d3-a456-426614174000",
                "proposed_volume": 50.0,
                "proposed_price": 0.12,
                "message": "I can provide this energy from my solar farm",
            }
        }


class SwapUpdateRequest(BaseModel):
    status: SwapStatus = Field(..., description="New status for the swap")
    message: Optional[str] = Field(
        None, max_length=1000, description="Optional response message"
    )


class SwapResponse(BaseModel):
    id: UUID
    listing_id: UUID
    initiator_id: UUID
    recipient_id: UUID
    proposed_volume: float
    proposed_price: Optional[float]
    status: str
    message: Optional[str]
    proposed_at: datetime
    responded_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class SwapDetailResponse(SwapResponse):
    """Extended swap response with related data"""

    listing_energy_type: Optional[str] = None
    listing_location: Optional[str] = None
    listing_volume: Optional[float] = None
    initiator_email: Optional[str] = None
    recipient_email: Optional[str] = None


class SwapListResponse(BaseModel):
    swaps: List[SwapResponse]
    total: int
    page: int = 1
    page_size: int = 20
