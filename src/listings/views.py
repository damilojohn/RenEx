from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from src.database.setup import get_db_session, AsyncSession
from src.auth.service import get_current_user
from src.auth.schemas import CurrentUser
from src.utils import CustomJSONResponse
from src.listings.schemas import (
    ListingCreateRequest,
    ListingUpdateRequest,
    ListingResponse,
    ListingFeedResponse,
    ListingDetailResponse,
)
from src.listings.service import (
    create_listing,
    get_listing_by_id,
    get_user_listings,
    update_listing,
    delete_listing,
    get_feed_listings,
    get_matching_listings,
)
from typing import Optional


base_router = APIRouter(prefix="/listings", tags=["Listings"])


@base_router.post(
    "/", response_model=ListingResponse, status_code=status.HTTP_201_CREATED
)
async def create_new_listing(
    listing_data: ListingCreateRequest,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new energy listing"""
    result = await create_listing(
        listing_data=listing_data, user_id=user.id, session=session
    )
    return CustomJSONResponse(
        status_code=status.HTTP_201_CREATED, content=result.model_dump()
    )


@base_router.get("/feed", response_model=ListingFeedResponse)
async def get_feed(
    listing_type: Optional[str] = Query(
        None, description="Filter by listing type: demand or supply"
    ),
    energy_type: Optional[str] = Query(
        None, description="Filter by energy type: solar or wind"
    ),
    location: Optional[str] = Query(None, description="Filter by location"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get feed of listings from other users"""
    result = await get_feed_listings(
        user_id=user.id,
        session=session,
        listing_type=listing_type,
        energy_type=energy_type,
        location=location,
        page=page,
        page_size=page_size,
    )
    return CustomJSONResponse(status_code=status.HTTP_200_OK,
                              content=result.model_dump())


@base_router.get("/me", response_model=list[ListingResponse])
async def get_my_listings(
    status_filter: Optional[str] = Query(
        None, description="Filter by status: active, inactive, completed, cancelled"
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get all listings created by the current user"""
    result = await get_user_listings(
        user_id=user.id,
        session=session,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )
    return CustomJSONResponse(
        status_code=status.HTTP_200_OK,
        content=[listing.model_dump() for listing in result],
    )


@base_router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: str,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get a specific listing by ID"""
    from uuid import UUID

    try:
        listing_uuid = UUID(listing_id)
    except ValueError:
        raise JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid listing ID format"},
        )

    result = await get_listing_by_id(listing_id=listing_uuid, session=session)
    return CustomJSONResponse(status_code=status.HTTP_200_OK, content=result.model_dump())


@base_router.put("/{listing_id}", response_model=ListingResponse)
async def update_my_listing(
    listing_id: str,
    update_data: ListingUpdateRequest,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Update a listing (only by owner)"""
    from uuid import UUID

    try:
        listing_uuid = UUID(listing_id)
    except ValueError:
        raise JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid listing ID format"},
        )

    result = await update_listing(
        listing_id=listing_uuid,
        user_id=user.id,
        update_data=update_data,
        session=session,
    )
    return CustomJSONResponse(status_code=status.HTTP_200_OK, content=result.model_dump())


@base_router.delete("/{listing_id}", status_code=status.HTTP_200_OK)
async def delete_my_listing(
    listing_id: str,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Delete a listing (only by owner)"""
    from uuid import UUID

    try:
        listing_uuid = UUID(listing_id)
    except ValueError:
        raise JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid listing ID format"},
        )

    result = await delete_listing(
        listing_id=listing_uuid, user_id=user.id, session=session
    )
    return CustomJSONResponse(status_code=status.HTTP_200_OK, content=result)


@base_router.get("/{listing_id}/matches", response_model=list[ListingResponse])
async def get_matching_listings_for_listing(
    listing_id: str,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get listings that match a specific listing (e.g., supply matches demand)"""
    from uuid import UUID

    try:
        listing_uuid = UUID(listing_id)
    except ValueError:
        raise JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid listing ID format"},
        )

    result = await get_matching_listings(user_listing_id=listing_uuid, session=session)
    return CustomJSONResponse(
        status_code=status.HTTP_200_OK,
        content=[listing.model_dump() for listing in result],
    )
