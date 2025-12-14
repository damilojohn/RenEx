from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from src.database.setup import get_db_session, AsyncSession
from src.auth.service import get_current_user
from src.auth.schemas import CurrentUser
from src.swaps.schemas import (
    SwapCreateRequest,
    SwapUpdateRequest,
    SwapResponse,
    SwapDetailResponse,
    SwapListResponse,
)
from src.swaps.service import (
    create_swap,
    get_swap_by_id,
    respond_to_swap,
    cancel_swap,
    complete_swap,
    get_user_swaps,
    get_swaps_for_listing,
)
from typing import Optional


base_router = APIRouter(prefix="/swaps", tags=["Swaps"])


@base_router.post("/", response_model=SwapResponse, status_code=status.HTTP_201_CREATED)
async def create_new_swap(
    swap_data: SwapCreateRequest,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new swap request for a listing"""
    result = await create_swap(
        swap_data=swap_data, initiator_id=user.id, session=session
    )
    return JSONResponse(
        status_code=status.HTTP_201_CREATED, content=result.model_dump()
    )


@base_router.get("/me", response_model=list[SwapResponse])
async def get_my_swaps(
    role: Optional[str] = Query(
        None, description="Filter by role: initiator or recipient"
    ),
    status_filter: Optional[str] = Query(
        None,
        description="Filter by status: pending, accepted, rejected, completed, cancelled",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get all swaps for the current user"""
    result = await get_user_swaps(
        user_id=user.id,
        session=session,
        role=role,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=[swap.model_dump() for swap in result]
    )


@base_router.get("/{swap_id}", response_model=SwapDetailResponse)
async def get_swap(
    swap_id: str,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get a specific swap by ID"""
    from uuid import UUID

    try:
        swap_uuid = UUID(swap_id)
    except ValueError:
        raise JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid swap ID format"},
        )

    result = await get_swap_by_id(swap_id=swap_uuid, session=session, user_id=user.id)
    return JSONResponse(status_code=status.HTTP_200_OK, content=result.model_dump())


@base_router.put("/{swap_id}/respond", response_model=SwapResponse)
async def respond_to_swap_request(
    swap_id: str,
    update_data: SwapUpdateRequest,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Accept or reject a swap request (only by recipient)"""
    from uuid import UUID

    try:
        swap_uuid = UUID(swap_id)
    except ValueError:
        raise JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid swap ID format"},
        )

    result = await respond_to_swap(
        swap_id=swap_uuid, user_id=user.id, update_data=update_data, session=session
    )
    return JSONResponse(status_code=status.HTTP_200_OK, content=result.model_dump())


@base_router.post("/{swap_id}/cancel", response_model=SwapResponse)
async def cancel_swap_request(
    swap_id: str,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Cancel a swap request (by initiator or recipient if pending)"""
    from uuid import UUID

    try:
        swap_uuid = UUID(swap_id)
    except ValueError:
        raise JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid swap ID format"},
        )

    result = await cancel_swap(swap_id=swap_uuid, user_id=user.id, session=session)
    return JSONResponse(status_code=status.HTTP_200_OK, content=result.model_dump())


@base_router.post("/{swap_id}/complete", response_model=SwapResponse)
async def complete_swap_request(
    swap_id: str,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Mark a swap as completed (only by recipient after acceptance)"""
    from uuid import UUID

    try:
        swap_uuid = UUID(swap_id)
    except ValueError:
        raise JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid swap ID format"},
        )

    result = await complete_swap(swap_id=swap_uuid, user_id=user.id, session=session)
    return JSONResponse(status_code=status.HTTP_200_OK, content=result.model_dump())


@base_router.get("/listing/{listing_id}", response_model=list[SwapResponse])
async def get_listing_swaps(
    listing_id: str,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get all swaps for a specific listing (only by listing owner)"""
    from uuid import UUID

    try:
        listing_uuid = UUID(listing_id)
    except ValueError:
        raise JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid listing ID format"},
        )

    result = await get_swaps_for_listing(
        listing_id=listing_uuid, user_id=user.id, session=session
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=[swap.model_dump() for swap in result]
    )
