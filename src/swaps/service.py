from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from src.swaps.models import Swap
from src.swaps.schemas import (
    SwapCreateRequest,
    SwapUpdateRequest,
    SwapResponse,
    SwapDetailResponse,
)
from src.swaps.enums import SwapStatus
from src.listings.models import Listings
from src.auth.models import RenExUser


async def create_swap(
    swap_data: SwapCreateRequest, initiator_id: UUID, session: AsyncSession
) -> SwapResponse:
    """Create a new swap request"""

    # Get the listing
    listing_result = await session.execute(
        select(Listings).filter(Listings.id == swap_data.listing_id)
    )
    listing = listing_result.scalar_one_or_none()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found"
        )

    # Check if listing is active
    if listing.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create swap for inactive listing",
        )

    # Check if user is trying to swap with their own listing
    if listing.user_id == initiator_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create swap for your own listing",
        )

    # Check if proposed volume is valid
    if swap_data.proposed_volume > listing.volume:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proposed volume ({swap_data.proposed_volume}) exceeds available volume ({listing.volume})",
        )

    # Check if there's already a pending swap for this listing from this user
    existing_swap = await session.execute(
        select(Swap).filter(
            and_(
                Swap.listing_id == swap_data.listing_id,
                Swap.initiator_id == initiator_id,
                Swap.status == SwapStatus.PENDING.value,
            )
        )
    )
    if existing_swap.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pending swap request for this listing",
        )

    try:
        new_swap = Swap(
            listing_id=swap_data.listing_id,
            initiator_id=initiator_id,
            recipient_id=listing.user_id,
            proposed_volume=swap_data.proposed_volume,
            proposed_price=swap_data.proposed_price,
            message=swap_data.message,
            status=SwapStatus.PENDING.value,
            proposed_at=datetime.now(timezone.utc),
        )

        session.add(new_swap)
        await session.commit()
        await session.refresh(new_swap)

        return SwapResponse.model_validate(new_swap)

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create swap: {str(e)}",
        )


async def get_swap_by_id(
    swap_id: UUID, session: AsyncSession, user_id: Optional[UUID] = None
) -> SwapDetailResponse:
    """Get a swap by ID with details"""

    result = await session.execute(select(Swap).filter(Swap.id == swap_id))
    swap = result.scalar_one_or_none()

    if not swap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Swap not found"
        )

    # Check if user has permission to view this swap
    if user_id and swap.initiator_id != user_id and swap.recipient_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this swap",
        )

    # Get related data
    listing_result = await session.execute(
        select(Listings).filter(Listings.id == swap.listing_id)
    )
    listing = listing_result.scalar_one_or_none()

    initiator_result = await session.execute(
        select(RenExUser).filter(RenExUser.id == swap.initiator_id)
    )
    initiator = initiator_result.scalar_one_or_none()

    recipient_result = await session.execute(
        select(RenExUser).filter(RenExUser.id == swap.recipient_id)
    )
    recipient = recipient_result.scalar_one_or_none()

    swap_dict = SwapResponse.model_validate(swap).model_dump()
    swap_dict.update(
        {
            "listing_energy_type": listing.energy_type if listing else None,
            "listing_location": listing.location if listing else None,
            "listing_volume": listing.volume if listing else None,
            "initiator_email": initiator.email if initiator else None,
            "recipient_email": recipient.email if recipient else None,
        }
    )

    return SwapDetailResponse(**swap_dict)


async def respond_to_swap(
    swap_id: UUID, user_id: UUID, update_data: SwapUpdateRequest, session: AsyncSession
) -> SwapResponse:
    """Accept or reject a swap request (only by recipient)"""

    result = await session.execute(
        select(Swap).filter(and_(Swap.id == swap_id, Swap.recipient_id == user_id))
    )
    swap = result.scalar_one_or_none()

    if not swap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Swap not found or you don't have permission to respond",
        )

    if swap.status != SwapStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update swap with status: {swap.status}",
        )

    # Validate status transition
    if update_data.status not in [SwapStatus.ACCEPTED.value, SwapStatus.REJECTED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only accept or reject a pending swap",
        )

    try:
        swap.status = update_data.status.value
        swap.responded_at = datetime.now(timezone.utc)

        if update_data.message:
            # Append response message if provided
            if swap.message:
                swap.message = f"{swap.message}\n\nResponse: {update_data.message}"
            else:
                swap.message = f"Response: {update_data.message}"

        await session.commit()
        await session.refresh(swap)

        return SwapResponse.model_validate(swap)

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update swap: {str(e)}",
        )


async def cancel_swap(
    swap_id: UUID, user_id: UUID, session: AsyncSession
) -> SwapResponse:
    """Cancel a swap (only by initiator or recipient if pending)"""

    result = await session.execute(
        select(Swap).filter(
            and_(
                Swap.id == swap_id,
                or_(Swap.initiator_id == user_id, Swap.recipient_id == user_id),
            )
        )
    )
    swap = result.scalar_one_or_none()

    if not swap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Swap not found or you don't have permission to cancel it",
        )

    if swap.status not in [SwapStatus.PENDING.value, SwapStatus.ACCEPTED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel swap with status: {swap.status}",
        )

    try:
        swap.status = SwapStatus.CANCELLED.value
        await session.commit()
        await session.refresh(swap)

        return SwapResponse.model_validate(swap)

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel swap: {str(e)}",
        )


async def complete_swap(
    swap_id: UUID, user_id: UUID, session: AsyncSession
) -> SwapResponse:
    """Mark a swap as completed (only by recipient after acceptance)"""

    result = await session.execute(
        select(Swap).filter(and_(Swap.id == swap_id, Swap.recipient_id == user_id))
    )
    swap = result.scalar_one_or_none()

    if not swap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Swap not found or you don't have permission to complete it",
        )

    if swap.status != SwapStatus.ACCEPTED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only complete an accepted swap",
        )

    try:
        swap.status = SwapStatus.COMPLETED.value
        swap.completed_at = datetime.now(timezone.utc)

        # Optionally update listing volume
        listing_result = await session.execute(
            select(Listings).filter(Listings.id == swap.listing_id)
        )
        listing = listing_result.scalar_one_or_none()

        if listing:
            # Reduce available volume
            listing.volume = max(0, listing.volume - swap.proposed_volume)
            if listing.volume == 0:
                listing.status = "completed"

        await session.commit()
        await session.refresh(swap)

        return SwapResponse.model_validate(swap)

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete swap: {str(e)}",
        )


async def get_user_swaps(
    user_id: UUID,
    session: AsyncSession,
    role: Optional[str] = None,  # "initiator" or "recipient"
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> List[SwapResponse]:
    """Get swaps for a user"""

    offset = (page - 1) * page_size

    query = select(Swap)

    if role == "initiator":
        query = query.filter(Swap.initiator_id == user_id)
    elif role == "recipient":
        query = query.filter(Swap.recipient_id == user_id)
    else:
        # Get all swaps where user is involved
        query = query.filter(
            or_(Swap.initiator_id == user_id, Swap.recipient_id == user_id)
        )

    if status_filter:
        query = query.filter(Swap.status == status_filter)

    query = query.order_by(desc(Swap.created_at)).limit(page_size).offset(offset)

    result = await session.execute(query)
    swaps = result.scalars().all()

    return [SwapResponse.model_validate(swap) for swap in swaps]


async def get_swaps_for_listing(
    listing_id: UUID, user_id: UUID, session: AsyncSession
) -> List[SwapResponse]:
    """Get all swaps for a specific listing (only by listing owner)"""

    # Verify user owns the listing
    listing_result = await session.execute(
        select(Listings).filter(
            and_(Listings.id == listing_id, Listings.user_id == user_id)
        )
    )
    listing = listing_result.scalar_one_or_none()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found or you don't have permission to view its swaps",
        )

    result = await session.execute(select(Swap).filter(Swap.listing_id == listing_id))
    swaps = result.scalars().all()

    return [SwapResponse.model_validate(swap) for swap in swaps]
