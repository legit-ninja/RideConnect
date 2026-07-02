import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.oauth_account import OAuthAccount, OAuthProvider
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OAuthProfile:
    provider: OAuthProvider
    provider_user_id: str
    email: str | None
    email_verified: bool


@dataclass(frozen=True)
class OAuthUserResult:
    user: User
    is_new_user: bool
    is_email_link: bool


class OAuthFlowError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def parse_google_profile(token: dict[str, Any]) -> OAuthProfile:
    userinfo = token.get("userinfo")
    if not isinstance(userinfo, dict):
        raise OAuthFlowError("provider_error", "Google did not return user profile data")

    subject = userinfo.get("sub")
    if not isinstance(subject, str) or not subject:
        raise OAuthFlowError("provider_error", "Google profile is missing subject identifier")

    email = userinfo.get("email")
    return OAuthProfile(
        provider=OAuthProvider.GOOGLE,
        provider_user_id=subject,
        email=email.lower() if isinstance(email, str) and email else None,
        email_verified=bool(userinfo.get("email_verified", False)),
    )


def parse_facebook_profile(data: dict[str, Any]) -> OAuthProfile:
    subject = data.get("id")
    if not isinstance(subject, str) or not subject:
        raise OAuthFlowError("provider_error", "Facebook profile is missing user identifier")

    email = data.get("email")
    normalized_email = email.lower() if isinstance(email, str) and email else None
    return OAuthProfile(
        provider=OAuthProvider.FACEBOOK,
        provider_user_id=subject,
        email=normalized_email,
        email_verified=bool(normalized_email),
    )


def resolve_oauth_user(db: Session, profile: OAuthProfile) -> OAuthUserResult:
    existing_oauth = db.scalar(
        select(OAuthAccount).where(
            OAuthAccount.provider == profile.provider,
            OAuthAccount.provider_user_id == profile.provider_user_id,
        )
    )

    if existing_oauth is not None:
        user = db.get(User, existing_oauth.user_id)
        if user is None:
            raise OAuthFlowError(
                "account_conflict",
                "OAuth identity is linked to a missing user account",
            )

        if (
            profile.email_verified
            and profile.email is not None
            and profile.email != user.email.lower()
        ):
            email_user = db.scalar(select(User).where(User.email == profile.email))
            if email_user is not None and email_user.id != user.id:
                raise OAuthFlowError(
                    "account_conflict",
                    "This provider account is already linked to a different user",
                )

        existing_oauth.provider_email = profile.email
        existing_oauth.provider_email_verified = profile.email_verified
        db.commit()
        db.refresh(user)
        return OAuthUserResult(user=user, is_new_user=False, is_email_link=False)

    if not profile.email_verified or profile.email is None:
        raise OAuthFlowError(
            "unverified_email",
            "A verified email from the provider is required to sign in",
        )

    user_by_email = db.scalar(select(User).where(User.email == profile.email))
    if user_by_email is not None:
        existing_provider_for_user = db.scalar(
            select(OAuthAccount).where(
                OAuthAccount.user_id == user_by_email.id,
                OAuthAccount.provider == profile.provider,
            )
        )
        if existing_provider_for_user is not None:
            raise OAuthFlowError(
                "account_conflict",
                "An account with this email already uses a different identity for this provider",
            )

        oauth_account = OAuthAccount(
            user_id=user_by_email.id,
            provider=profile.provider,
            provider_user_id=profile.provider_user_id,
            provider_email=profile.email,
            provider_email_verified=profile.email_verified,
        )
        db.add(oauth_account)
        db.commit()
        db.refresh(user_by_email)
        return OAuthUserResult(
            user=user_by_email,
            is_new_user=False,
            is_email_link=True,
        )

    user = User(
        email=profile.email,
        password_hash=None,
        is_rider=False,
        is_owner=False,
        is_admin=False,
    )
    db.add(user)
    db.flush()

    oauth_account = OAuthAccount(
        user_id=user.id,
        provider=profile.provider,
        provider_user_id=profile.provider_user_id,
        provider_email=profile.email,
        provider_email_verified=profile.email_verified,
    )
    db.add(oauth_account)
    db.commit()
    db.refresh(user)
    return OAuthUserResult(user=user, is_new_user=True, is_email_link=False)


def log_oauth_attempt(
    *,
    provider: OAuthProvider,
    outcome: str,
    user_id: UUID | None = None,
    is_new_user: bool | None = None,
    is_email_link: bool | None = None,
    error_reason: str | None = None,
) -> None:
    logger.info(
        "oauth_attempt provider=%s outcome=%s user_id=%s is_new_user=%s "
        "is_email_link=%s error_reason=%s",
        provider.value,
        outcome,
        str(user_id) if user_id else None,
        is_new_user,
        is_email_link,
        error_reason,
    )


def oauth_error_redirect(code: str, message: str) -> RedirectResponse:
    params = urlencode({"error": code, "message": message})
    return RedirectResponse(
        url=f"{settings.frontend_oauth_error_url}?{params}",
        status_code=302,
    )


def oauth_success_redirect(access_token: str, *, is_new_user: bool) -> RedirectResponse:
    params: dict[str, str] = {"access_token": access_token}
    if is_new_user:
        params["new_user"] = "true"
    return RedirectResponse(
        url=f"{settings.frontend_oauth_success_url}?{urlencode(params)}",
        status_code=302,
    )
