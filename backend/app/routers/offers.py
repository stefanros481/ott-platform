"""Offers router — TVOD purchase endpoint (rent / buy).

Rate-limited to 10 requests/hour per user (FR-025).
Auth is required: guests must log in before purchasing.
"""

import uuid

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import and_, select

from app.dependencies import CurrentUser, DB, RedisClient
from app.limiter import limiter
from app.models.entitlement import TitleOffer
from app.schemas.entitlement import TVODPurchaseRequest, TVODPurchaseResponse

router = APIRouter()


@router.post(
    "/titles/{title_id}/purchase",
    response_model=TVODPurchaseResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/hour")
async def purchase_title(
    request: Request,
    title_id: uuid.UUID,
    body: TVODPurchaseRequest,
    user: CurrentUser,
    db: DB,
    redis: RedisClient,
) -> TVODPurchaseResponse:
    """Rent or buy a title.

    Creates a UserEntitlement with source_type='tvod'.
    Free titles are accessed directly and do not require a purchase — this
    endpoint rejects offer_type='free' at the schema level (Literal["rent","buy"]).

    Returns 404 if no active offer of the requested type exists.
    Returns 409 if the user already has an active entitlement of this type.
    Returns 429 if the rate limit (10/hour) is exceeded.
    """
    from app.services import entitlement_service

    # Fetch the active offer upfront to get price/currency for the response.
    # The service validates the offer again atomically — this fetch is only for
    # building the response body.
    offer_result = await db.execute(
        select(TitleOffer).where(
            and_(
                TitleOffer.title_id == title_id,
                TitleOffer.offer_type == body.offer_type,
                TitleOffer.is_active.is_(True),
            )
        )
    )
    offer = offer_result.scalar_one_or_none()
    if offer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active {body.offer_type} offer found for this title",
        )

    try:
        entitlement = await entitlement_service.create_tvod_entitlement(
            user.id, title_id, body.offer_type, db, redis
        )
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active {body.offer_type} offer found for this title",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    return TVODPurchaseResponse(
        entitlement_id=entitlement.id,
        title_id=title_id,
        offer_type=body.offer_type,
        expires_at=entitlement.expires_at,
        price_cents=offer.price_cents,
        currency=offer.currency,
    )
