from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from src.listings.models import Listings
from src.listings.schemas import (
    ListingCreateRequest,
    ListingUpdateRequest,
    ListingResponse,
    ListingFeedResponse,
)
from src.auth.models import RenExUser


async def create_listing(
    listing_data: ListingCreateRequest, user_id: UUID, session: AsyncSession
) -> ListingResponse:
    """Create a new energy listing"""

    # Validate time range
    if listing_data.start_time >= listing_data.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time must be before end time",
        )

    # Check if user exists
    user_result = await session.execute(
        select(RenExUser).filter(RenExUser.id == user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    try:
        new_listing = Listings(
            listing_type=listing_data.listing_type.value,
            energy_type=listing_data.energy_type.value,
            volume=listing_data.volume,
            price=listing_data.price,
            location=listing_data.location,
            start_time=listing_data.start_time,
            end_time=listing_data.end_time,
            description=listing_data.description,
            user_id=user_id,
            status="active",
        )

        session.add(new_listing)
        await session.commit()
        await session.refresh(new_listing)

        return ListingResponse.model_validate(new_listing)

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create listing: {str(e)}",
        )


async def get_listing_by_id(
    listing_id: UUID, session: AsyncSession, user_id: Optional[UUID] = None
) -> ListingResponse:
    """Get a listing by ID"""

    result = await session.execute(select(Listings).filter(Listings.id == listing_id))
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found"
        )

    return ListingResponse.model_validate(listing)


async def get_user_listings(
    user_id: UUID,
    session: AsyncSession,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[ListingResponse]:
    """Get all listings for a specific user"""

    query = select(Listings).filter(Listings.user_id == user_id)

    if status_filter:
        query = query.filter(Listings.status == status_filter)

    query = query.order_by(desc(Listings.created_at)).limit(limit).offset(offset)

    result = await session.execute(query)
    listings = result.scalars().all()

    return [ListingResponse.model_validate(listing) for listing in listings]


async def update_listing(
    listing_id: UUID,
    user_id: UUID,
    update_data: ListingUpdateRequest,
    session: AsyncSession,
) -> ListingResponse:
    """Update a listing (only by owner)"""

    result = await session.execute(
        select(Listings).filter(
            and_(Listings.id == listing_id, Listings.user_id == user_id)
        )
    )
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found or you don't have permission to update it",
        )

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)

    # Validate time range if both times are being updated
    if update_dict.get("start_time") and update_dict.get("end_time"):
        if update_dict["start_time"] >= update_dict["end_time"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time must be before end time",
            )
    elif update_dict.get("start_time") and listing.end_time:
        if update_dict["start_time"] >= listing.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time must be before end time",
            )
    elif update_dict.get("end_time") and listing.start_time:
        if listing.start_time >= update_dict["end_time"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time must be before end time",
            )

    for field, value in update_dict.items():
        setattr(listing, field, value)

    try:
        await session.commit()
        await session.refresh(listing)
        return ListingResponse.model_validate(listing)
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update listing: {str(e)}",
        )


async def delete_listing(
    listing_id: UUID, user_id: UUID, session: AsyncSession
) -> dict:
    """Delete a listing (only by owner)"""

    result = await session.execute(
        select(Listings).filter(
            and_(Listings.id == listing_id, Listings.user_id == user_id)
        )
    )
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found or you don't have permission to delete it",
        )

    try:
        await session.delete(listing)
        await session.commit()
        return {"message": "Listing deleted successfully"}
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete listing: {str(e)}",
        )


async def get_feed_listings(
    user_id: UUID,
    session: AsyncSession,
    listing_type: Optional[str] = None,
    energy_type: Optional[str] = None,
    location: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> ListingFeedResponse:
    """Get feed of listings from other users (excluding current user's listings)"""

    offset = (page - 1) * page_size

    # Build query - exclude user's own listings and only show active listings
    query = select(Listings).filter(
        and_(Listings.user_id != user_id, Listings.status == "active")
    )

    # Apply filters
    if listing_type:
        query = query.filter(Listings.listing_type == listing_type)

    if energy_type:
        query = query.filter(Listings.energy_type == energy_type)

    if location:
        # Simple location matching (can be enhanced with geolocation)
        query = query.filter(Listings.location.ilike(f"%{location}%"))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(desc(Listings.created_at)).limit(page_size).offset(offset)
    result = await session.execute(query)
    listings = result.scalars().all()

    return ListingFeedResponse(
        listings=[ListingResponse.model_validate(listing) for listing in listings],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_matching_listings(
    user_listing_id: UUID, session: AsyncSession
) -> List[ListingResponse]:
    """Get listings that match a user's listing (e.g., supply matches demand)"""

    # Get the user's listing
    result = await session.execute(
        select(Listings).filter(Listings.id == user_listing_id)
    )
    user_listing = result.scalar_one_or_none()

    if not user_listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found"
        )

    # Find matching listings
    # If user has a supply listing, find demand listings (and vice versa)
    opposite_type = "demand" if user_listing.listing_type == "supply" else "supply"

    query = select(Listings).filter(
        and_(
            Listings.user_id != user_listing.user_id,
            Listings.listing_type == opposite_type,
            Listings.energy_type == user_listing.energy_type,
            Listings.status == "active",
            # Time overlap
            Listings.start_time <= user_listing.end_time,
            Listings.end_time >= user_listing.start_time,
        )
    )

    result = await session.execute(query)
    listings = result.scalars().all()

    return [ListingResponse.model_validate(listing) for listing in listings]
