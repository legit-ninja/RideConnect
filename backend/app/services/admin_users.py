from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.animal import Animal
from app.models.listing import Listing
from app.models.oauth_account import OAuthAccount
from app.models.user import User, VerificationStatus
from app.schemas.admin import AdminGuardianSummary, AdminUserDetail, AdminUserSummary


def user_to_summary(user: User) -> AdminUserSummary:
    oauth_providers = [account.provider for account in user.oauth_accounts]
    return AdminUserSummary(
        id=user.id,
        email=user.email,
        is_rider=user.is_rider,
        is_owner=user.is_owner,
        is_horse_trainer=user.is_horse_trainer,
        is_riding_instructor=user.is_riding_instructor,
        trainer_verified=user.trainer_verified,
        is_admin=user.is_admin,
        verification_status=user.verification_status,
        is_minor=user.is_minor,
        rider_skill_level=user.rider_skill_level,
        oauth_providers=oauth_providers,
        created_at=user.created_at,
    )


def _guardian_summary(user: User) -> AdminGuardianSummary | None:
    if user.guardian is None:
        return None
    return AdminGuardianSummary(
        id=user.guardian.id,
        email=user.guardian.email,
        verification_status=user.guardian.verification_status,
    )


def user_to_detail(
    user: User,
    *,
    animal_count: int = 0,
    listing_count: int = 0,
    active_listing_count: int = 0,
) -> AdminUserDetail:
    summary = user_to_summary(user)
    return AdminUserDetail(
        **summary.model_dump(),
        phone=user.phone,
        guardian_user_id=user.guardian_user_id,
        guardian=_guardian_summary(user),
        oauth_accounts=list(user.oauth_accounts),
        animal_count=animal_count,
        listing_count=listing_count,
        active_listing_count=active_listing_count,
    )


def get_user_detail(db: Session, user_id: UUID) -> User | None:
    return db.scalar(
        select(User)
        .options(
            selectinload(User.oauth_accounts),
            selectinload(User.guardian),
        )
        .where(User.id == user_id)
    )


def get_user_marketplace_counts(
    db: Session, user_id: UUID
) -> tuple[int, int, int]:
    animal_count = (
        db.scalar(
            select(func.count()).select_from(Animal).where(Animal.owner_id == user_id)
        )
        or 0
    )
    listing_count = (
        db.scalar(
            select(func.count()).select_from(Listing).where(Listing.owner_id == user_id)
        )
        or 0
    )
    active_listing_count = (
        db.scalar(
            select(func.count())
            .select_from(Listing)
            .where(Listing.owner_id == user_id, Listing.active.is_(True))
        )
        or 0
    )
    return animal_count, listing_count, active_listing_count


def list_users(
    db: Session,
    *,
    q: str | None,
    verification_status: VerificationStatus | None,
    is_admin: bool | None,
    limit: int,
    offset: int,
) -> tuple[list[User], int]:
    base = select(User).options(selectinload(User.oauth_accounts))
    count_query = select(func.count()).select_from(User)

    if q:
        pattern = f"%{q.strip().lower()}%"
        email_filter = func.lower(User.email).like(pattern)
        base = base.where(email_filter)
        count_query = count_query.where(email_filter)

    if verification_status is not None:
        base = base.where(User.verification_status == verification_status)
        count_query = count_query.where(User.verification_status == verification_status)

    if is_admin is not None:
        base = base.where(User.is_admin.is_(is_admin))
        count_query = count_query.where(User.is_admin.is_(is_admin))

    total = db.scalar(count_query) or 0
    users = list(
        db.scalars(
            base.order_by(User.created_at.desc()).limit(limit).offset(offset)
        ).all()
    )
    return users, total


def count_oauth_users(db: Session) -> int:
    return (
        db.scalar(
            select(func.count(func.distinct(OAuthAccount.user_id))).select_from(
                OAuthAccount
            )
        )
        or 0
    )


def count_signups_since(db: Session, since: datetime) -> int:
    return (
        db.scalar(
            select(func.count()).select_from(User).where(User.created_at >= since)
        )
        or 0
    )


def count_by_verification(db: Session, status: VerificationStatus) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.verification_status == status)
        )
        or 0
    )
