from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.dependencies import require_admin
from app.models.admin_audit_log import AdminAuditAction
from app.models.animal import Animal
from app.models.listing import Listing
from app.models.platform_flag import PlatformFlag
from app.models.user import User, VerificationStatus
from app.schemas.admin import (
    AdminAuditLogEntry,
    AdminAuditLogListResponse,
    AdminListingListResponse,
    AdminListingSummary,
    AdminPlatformFlagSummary,
    AdminPlatformFlagListResponse,
    AdminStatsResponse,
    AdminUserDetail,
    AdminUserListResponse,
    AdminUserSummary,
    UpdateListingActiveRequest,
    UpdateUserRolesRequest,
    UpdateTrainerVerificationRequest,
    UpdateVerificationRequest,
)
from app.services.admin_audit import list_audit_logs, log_admin_action
from app.services.events import log_event
from app.services.admin_users import (
    count_by_verification,
    count_oauth_users,
    count_signups_since,
    get_user_detail,
    get_user_marketplace_counts,
    list_users,
    user_to_detail,
    user_to_summary,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsResponse)
def admin_stats(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> AdminStatsResponse:
    # Authz: require_admin ensures caller has is_admin=True.
    total_users = db.scalar(select(func.count()).select_from(User)) or 0
    admin_users = (
        db.scalar(select(func.count()).select_from(User).where(User.is_admin.is_(True)))
        or 0
    )
    verified_users = count_by_verification(db, VerificationStatus.VERIFIED)
    unverified_users = count_by_verification(db, VerificationStatus.UNVERIFIED)
    pending_users = count_by_verification(db, VerificationStatus.PENDING)
    rejected_users = count_by_verification(db, VerificationStatus.REJECTED)
    rider_users = (
        db.scalar(select(func.count()).select_from(User).where(User.is_rider.is_(True)))
        or 0
    )
    owner_users = (
        db.scalar(select(func.count()).select_from(User).where(User.is_owner.is_(True)))
        or 0
    )
    oauth_users = count_oauth_users(db)
    signups_last_7d = count_signups_since(
        db, datetime.now(UTC) - timedelta(days=7)
    )
    total_animals = db.scalar(select(func.count()).select_from(Animal)) or 0
    total_listings = db.scalar(select(func.count()).select_from(Listing)) or 0
    active_listings = (
        db.scalar(
            select(func.count()).select_from(Listing).where(Listing.active.is_(True))
        )
        or 0
    )

    return AdminStatsResponse(
        total_users=total_users,
        admin_users=admin_users,
        verified_users=verified_users,
        unverified_users=unverified_users,
        pending_users=pending_users,
        rejected_users=rejected_users,
        rider_users=rider_users,
        owner_users=owner_users,
        oauth_users=oauth_users,
        signups_last_7d=signups_last_7d,
        total_animals=total_animals,
        total_listings=total_listings,
        active_listings=active_listings,
    )


@router.get("/users", response_model=AdminUserListResponse)
def admin_list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
    q: str | None = Query(default=None, max_length=255),
    verification_status: VerificationStatus | None = None,
    is_admin: bool | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AdminUserListResponse:
    # Authz: require_admin — only admins may list all users.
    users, total = list_users(
        db,
        q=q,
        verification_status=verification_status,
        is_admin=is_admin,
        limit=limit,
        offset=offset,
    )
    return AdminUserListResponse(
        items=[user_to_summary(user) for user in users],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def admin_get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> AdminUserDetail:
    # Authz: require_admin — only admins may view full user records.
    user = get_user_detail(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    animal_count, listing_count, active_listing_count = get_user_marketplace_counts(
        db, user.id
    )
    return user_to_detail(
        user,
        animal_count=animal_count,
        listing_count=listing_count,
        active_listing_count=active_listing_count,
    )


@router.patch("/users/{user_id}/verification", response_model=AdminUserDetail)
def admin_update_verification(
    user_id: UUID,
    payload: UpdateVerificationRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> AdminUserDetail:
    # Authz: require_admin — manual KYC queue; does not auto-verify via OAuth.
    user = get_user_detail(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    previous_status = user.verification_status
    user.verification_status = payload.verification_status

    if (
        previous_status != VerificationStatus.VERIFIED
        and payload.verification_status == VerificationStatus.VERIFIED
    ):
        log_event(db, "verification_completed", user_id=user.id)

    log_admin_action(
        db,
        actor=admin,
        action=AdminAuditAction.VERIFICATION_STATUS_CHANGED,
        target_user_id=user.id,
        metadata={
            "previous_status": previous_status.value,
            "new_status": payload.verification_status.value,
            "note": payload.note,
        },
    )
    db.commit()
    db.refresh(user)
    user = get_user_detail(db, user_id)
    assert user is not None
    animal_count, listing_count, active_listing_count = get_user_marketplace_counts(
        db, user.id
    )
    return user_to_detail(
        user,
        animal_count=animal_count,
        listing_count=listing_count,
        active_listing_count=active_listing_count,
    )


@router.patch("/users/{user_id}/roles", response_model=AdminUserDetail)
def admin_update_roles(
    user_id: UUID,
    payload: UpdateUserRolesRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> AdminUserDetail:
    # Authz: require_admin — admins may set rider/owner flags (e.g. OAuth onboarding gap).
    user = get_user_detail(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    previous_roles = {
        "is_rider": user.is_rider,
        "is_owner": user.is_owner,
    }
    user.is_rider = payload.is_rider
    user.is_owner = payload.is_owner

    log_admin_action(
        db,
        actor=admin,
        action=AdminAuditAction.USER_ROLES_CHANGED,
        target_user_id=user.id,
        metadata={
            "previous": previous_roles,
            "new": {
                "is_rider": payload.is_rider,
                "is_owner": payload.is_owner,
            },
        },
    )
    db.commit()
    db.refresh(user)
    user = get_user_detail(db, user_id)
    assert user is not None
    animal_count, listing_count, active_listing_count = get_user_marketplace_counts(
        db, user.id
    )
    return user_to_detail(
        user,
        animal_count=animal_count,
        listing_count=listing_count,
        active_listing_count=active_listing_count,
    )


@router.patch("/users/{user_id}/trainer-verification", response_model=AdminUserDetail)
def admin_update_trainer_verification(
    user_id: UUID,
    payload: UpdateTrainerVerificationRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> AdminUserDetail:
    # Authz: require_admin — admins may set verified-trainer badge (credential tier placeholder).
    user = get_user_detail(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    previous = user.trainer_verified
    user.trainer_verified = payload.trainer_verified
    log_admin_action(
        db,
        actor=admin,
        action=AdminAuditAction.USER_ROLES_CHANGED,
        target_user_id=user.id,
        metadata={
            "field": "trainer_verified",
            "previous": previous,
            "new": payload.trainer_verified,
            "note": payload.note,
        },
    )
    db.commit()
    db.refresh(user)
    user = get_user_detail(db, user_id)
    assert user is not None
    animal_count, listing_count, active_listing_count = get_user_marketplace_counts(
        db, user.id
    )
    return user_to_detail(
        user,
        animal_count=animal_count,
        listing_count=listing_count,
        active_listing_count=active_listing_count,
    )


@router.get("/listings", response_model=AdminListingListResponse)
def admin_list_listings(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
    active: bool | None = None,
    owner_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AdminListingListResponse:
    # Authz: require_admin — admins may view all listings for moderation.
    base = (
        select(Listing)
        .join(User, Listing.owner_id == User.id)
        .options(selectinload(Listing.animal), selectinload(Listing.owner))
    )
    count_stmt = select(func.count()).select_from(Listing)
    if active is not None:
        base = base.where(Listing.active.is_(active))
        count_stmt = count_stmt.where(Listing.active.is_(active))
    if owner_id is not None:
        base = base.where(Listing.owner_id == owner_id)
        count_stmt = count_stmt.where(Listing.owner_id == owner_id)

    total = db.scalar(count_stmt) or 0
    listings = list(
        db.scalars(
            base.order_by(Listing.created_at.desc()).limit(limit).offset(offset)
        ).all()
    )
    items = [
        AdminListingSummary(
            id=listing.id,
            animal_name=listing.animal.name,
            owner_email=listing.owner.email,
            activity_type=listing.activity_type.value,
            price=listing.price,
            availability=listing.availability,
            active=listing.active,
            created_at=listing.created_at,
        )
        for listing in listings
    ]
    return AdminListingListResponse(items=items, total=total)


@router.patch("/listings/{listing_id}", response_model=AdminListingSummary)
def admin_update_listing_active(
    listing_id: UUID,
    payload: UpdateListingActiveRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> AdminListingSummary:
    # Authz: require_admin — admins may activate/deactivate listings for moderation.
    listing = db.scalar(
        select(Listing)
        .options(selectinload(Listing.animal), selectinload(Listing.owner))
        .where(Listing.id == listing_id)
    )
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    previous_active = listing.active
    listing.active = payload.active
    action = (
        AdminAuditAction.LISTING_REACTIVATED
        if payload.active
        else AdminAuditAction.LISTING_DEACTIVATED
    )
    log_admin_action(
        db,
        actor=admin,
        action=action,
        target_user_id=listing.owner_id,
        metadata={
            "listing_id": str(listing.id),
            "previous_active": previous_active,
            "new_active": payload.active,
        },
    )
    db.commit()
    db.refresh(listing)
    return AdminListingSummary(
        id=listing.id,
        animal_name=listing.animal.name,
        owner_email=listing.owner.email,
        activity_type=listing.activity_type.value,
        price=listing.price,
        availability=listing.availability,
        active=listing.active,
        created_at=listing.created_at,
    )


@router.get("/audit", response_model=AdminAuditLogListResponse)
def admin_list_audit(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
    actor_id: UUID | None = None,
    target_user_id: UUID | None = None,
    action: AdminAuditAction | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AdminAuditLogListResponse:
    # Authz: require_admin — only admins may read moderation audit history.
    entries, total = list_audit_logs(
        db,
        actor_id=actor_id,
        target_user_id=target_user_id,
        action=action,
        created_after=created_after,
        created_before=created_before,
        limit=limit,
        offset=offset,
    )
    items = [
        AdminAuditLogEntry(
            id=entry.id,
            actor_id=entry.actor_id,
            actor_email=entry.actor.email,
            action=entry.action.value,
            target_user_id=entry.target_user_id,
            target_user_email=(
                entry.target_user.email if entry.target_user is not None else None
            ),
            metadata=entry.metadata_,
            created_at=entry.created_at,
        )
        for entry in entries
    ]
    return AdminAuditLogListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.get("/flags", response_model=AdminPlatformFlagListResponse)
def admin_list_flags(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
    unresolved_only: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AdminPlatformFlagListResponse:
    # Authz: require_admin — trust & safety pattern flags for manual review.
    base = select(PlatformFlag).options(selectinload(PlatformFlag.user))
    count_stmt = select(func.count()).select_from(PlatformFlag)
    if unresolved_only:
        base = base.where(PlatformFlag.resolved_at.is_(None))
        count_stmt = count_stmt.where(PlatformFlag.resolved_at.is_(None))

    total = db.scalar(count_stmt) or 0
    flags = list(
        db.scalars(
            base.order_by(PlatformFlag.created_at.desc()).limit(limit).offset(offset)
        ).all()
    )
    items = [
        AdminPlatformFlagSummary(
            id=flag.id,
            user_id=flag.user_id,
            user_email=flag.user.email,
            flag_type=flag.flag_type.value,
            details=flag.details,
            created_at=flag.created_at,
            resolved_at=flag.resolved_at,
        )
        for flag in flags
    ]
    return AdminPlatformFlagListResponse(items=items, total=total)
