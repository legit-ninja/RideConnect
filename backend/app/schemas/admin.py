from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.oauth_account import OAuthProvider
from app.models.user import VerificationStatus


class OAuthAccountSummary(BaseModel):
    provider: OAuthProvider
    provider_email: str | None
    provider_email_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminGuardianSummary(BaseModel):
    id: UUID
    email: str
    verification_status: VerificationStatus


class AdminUserSummary(BaseModel):
    id: UUID
    email: str
    is_rider: bool
    is_owner: bool
    is_horse_trainer: bool
    is_riding_instructor: bool
    trainer_verified: bool
    is_admin: bool
    verification_status: VerificationStatus
    is_minor: bool
    rider_skill_level: int | None = None
    oauth_providers: list[OAuthProvider]
    created_at: datetime


class AdminUserDetail(AdminUserSummary):
    phone: str | None
    guardian_user_id: UUID | None
    guardian: AdminGuardianSummary | None = None
    oauth_accounts: list[OAuthAccountSummary]
    animal_count: int = 0
    listing_count: int = 0
    active_listing_count: int = 0


class AdminUserListResponse(BaseModel):
    items: list[AdminUserSummary]
    total: int
    limit: int
    offset: int


class AdminStatsResponse(BaseModel):
    total_users: int
    admin_users: int
    verified_users: int
    unverified_users: int
    pending_users: int
    rejected_users: int
    rider_users: int
    owner_users: int
    oauth_users: int
    signups_last_7d: int
    total_animals: int
    total_listings: int
    active_listings: int


class AdminListingSummary(BaseModel):
    id: UUID
    animal_name: str
    owner_email: str
    activity_type: str
    price: Decimal
    availability: str | None
    active: bool
    created_at: datetime


class AdminListingListResponse(BaseModel):
    items: list[AdminListingSummary]
    total: int


class UpdateListingActiveRequest(BaseModel):
    active: bool


class UpdateVerificationRequest(BaseModel):
    verification_status: VerificationStatus
    note: str | None = Field(default=None, max_length=500)


class UpdateUserRolesRequest(BaseModel):
    is_rider: bool
    is_owner: bool


class UpdateTrainerVerificationRequest(BaseModel):
    trainer_verified: bool
    note: str | None = Field(default=None, max_length=500)


class AdminAuditLogEntry(BaseModel):
    id: UUID
    actor_id: UUID
    actor_email: str
    action: str
    target_user_id: UUID | None
    target_user_email: str | None
    metadata: dict
    created_at: datetime


class AdminAuditLogListResponse(BaseModel):
    items: list[AdminAuditLogEntry]
    total: int
    limit: int
    offset: int


class AdminPlatformFlagSummary(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str
    flag_type: str
    details: dict | None
    created_at: datetime
    resolved_at: datetime | None


class AdminPlatformFlagListResponse(BaseModel):
    items: list[AdminPlatformFlagSummary]
    total: int
