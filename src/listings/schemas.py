from pydantic import BaseModel, Field
from datetime import datetime
from src.listings.enums import ListingType, EnergyType
from typing import List, Optional
from uuid import UUID


class ListingCreateRequest(BaseModel):
    listing_type: ListingType = Field(
        ..., description="Type of listing: demand or supply"
    )
    energy_type: EnergyType = Field(..., description="Type of energy: solar or wind")
    volume: float = Field(..., gt=0, description="Volume of energy in kWh")
    price: float = Field(..., gt=0, description="Price per kWh")
    location: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Location of the farm/energy source",
    )
    start_time: datetime = Field(
        ..., description="Start time for energy availability/need"
    )
    end_time: datetime = Field(..., description="End time for energy availability/need")
    description: Optional[str] = Field(
        None, max_length=1000, description="Optional description of the listing"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "listing_type": "supply",
                "energy_type": "solar",
                "volume": 100.5,
                "price": 0.15,
                "location": "Lagos, Nigeria",
                "start_time": "2024-01-15T08:00:00Z",
                "end_time": "2024-01-15T18:00:00Z",
                "description": "Excess solar energy from farm panels",
            }
        }


class ListingUpdateRequest(BaseModel):
    volume: Optional[float] = Field(None, gt=0)
    price: Optional[float] = Field(None, gt=0)
    location: Optional[str] = Field(None, min_length=1, max_length=500)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(
        None, pattern="^(active|inactive|completed|cancelled)$"
    )


class ListingResponse(BaseModel):
    id: UUID
    listing_type: str
    energy_type: str
    volume: float
    price: float
    location: str
    start_time: datetime
    end_time: datetime
    status: str
    description: Optional[str]
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ListingFeedResponse(BaseModel):
    listings: List[ListingResponse]
    total: int
    page: int = 1
    page_size: int = 20


class ListingDetailResponse(ListingResponse):
    user_email: Optional[str] = None
    user_first_name: Optional[str] = None
    user_last_name: Optional[str] = None
