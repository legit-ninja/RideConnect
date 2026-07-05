import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.booking_request import BookingRequest, BookingStatus
from app.models.family_member import FamilyMember
from app.models.user import RiderType, User, VerificationStatus
from app.schemas.family import FamilyMemberInput, UpdateFamilyProfileRequest

OPEN_BOOKING_STATUSES = (
    BookingStatus.PENDING_PAYMENT,
    BookingStatus.PENDING_OWNER,
    BookingStatus.APPROVED,
)


def list_family_members(db: Session, user_id: uuid.UUID) -> list[FamilyMember]:
    return list(
        db.scalars(
            select(FamilyMember)
            .where(FamilyMember.user_id == user_id)
            .order_by(FamilyMember.sort_order, FamilyMember.created_at)
        ).all()
    )


def has_open_family_bookings(db: Session, user_id: uuid.UUID) -> bool:
    return (
        db.scalar(
            select(func.count())
            .select_from(BookingRequest)
            .where(
                BookingRequest.rider_id == user_id,
                BookingRequest.family_booking_group_id.is_not(None),
                BookingRequest.status.in_(OPEN_BOOKING_STATUSES),
            )
        )
        or 0
    ) > 0


def validate_family_profile(user: User, payload: UpdateFamilyProfileRequest) -> None:
    if user.is_minor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minor accounts cannot configure a family profile",
        )

    if payload.rider_type == RiderType.INDIVIDUAL:
        return

    if not payload.family_name or not payload.family_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Family name is required for family rider type",
        )
    if payload.family_size is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Family size is required for family rider type",
        )
    if payload.members is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Family roster is required for family rider type",
        )
    if len(payload.members) != payload.family_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Roster must contain exactly family_size members",
        )

    has_minor = any(m.is_minor for m in payload.members)
    if has_minor and user.verification_status != VerificationStatus.VERIFIED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verified account required to add minor family members to roster",
        )


def apply_family_profile(
    db: Session,
    user: User,
    payload: UpdateFamilyProfileRequest,
) -> list[FamilyMember]:
    if payload.rider_type == RiderType.INDIVIDUAL:
        if user.rider_type == RiderType.FAMILY and has_open_family_bookings(db, user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot switch to individual while open family bookings exist",
            )
        user.rider_type = RiderType.INDIVIDUAL
        user.family_name = None
        user.family_size = None
        for member in list(user.family_members):
            db.delete(member)
        db.flush()
        return []

    validate_family_profile(user, payload)
    assert payload.family_name is not None
    assert payload.family_size is not None
    assert payload.members is not None

    user.rider_type = RiderType.FAMILY
    user.family_name = payload.family_name.strip()
    user.family_size = payload.family_size
    user.rider_skill_level = None

    for member in list(user.family_members):
        db.delete(member)
    db.flush()

    created: list[FamilyMember] = []
    for idx, item in enumerate(_normalize_members(payload.members)):
        member = FamilyMember(
            user_id=user.id,
            display_name=item.display_name.strip(),
            rider_skill_level=item.rider_skill_level,
            is_minor=item.is_minor,
            sort_order=item.sort_order if item.sort_order else idx,
        )
        db.add(member)
        created.append(member)
    db.flush()
    return created


def _normalize_members(members: list[FamilyMemberInput]) -> list[FamilyMemberInput]:
    return [
        FamilyMemberInput(
            display_name=m.display_name,
            rider_skill_level=m.rider_skill_level,
            is_minor=m.is_minor,
            sort_order=m.sort_order if m.sort_order else idx,
        )
        for idx, m in enumerate(members)
    ]


def get_roster_members(
    db: Session,
    user: User,
    member_ids: list[uuid.UUID],
) -> list[FamilyMember]:
    if user.rider_type != RiderType.FAMILY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Family member booking requires a family rider profile",
        )
    members = list(
        db.scalars(
            select(FamilyMember).where(
                FamilyMember.user_id == user.id,
                FamilyMember.id.in_(member_ids),
            )
        ).all()
    )
    if len(members) != len(set(member_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more family members were not found on your roster",
        )
    return sorted(members, key=lambda m: (m.sort_order, m.created_at))
