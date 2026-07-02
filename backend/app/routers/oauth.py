from authlib.integrations.base_client.errors import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.oauth_account import OAuthProvider
from app.services.oauth import (
    OAuthFlowError,
    log_oauth_attempt,
    oauth_error_redirect,
    oauth_success_redirect,
    parse_facebook_profile,
    parse_google_profile,
    resolve_oauth_user,
)
from app.services.oauth_client import oauth
from app.services.security import create_access_token

router = APIRouter(prefix="/auth", tags=["oauth"])


def _require_google_config() -> None:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured",
        )
    if not settings.google_redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth redirect URI is not configured",
        )


def _require_facebook_config() -> None:
    if not settings.facebook_app_id or not settings.facebook_app_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Facebook OAuth is not configured",
        )
    if not settings.facebook_redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Facebook OAuth redirect URI is not configured",
        )


@router.get("/google/login")
async def google_login(request: Request) -> RedirectResponse:
    # Authz: public entry point; redirects browser to Google consent (state managed by Authlib).
    _require_google_config()
    return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    # Authz: public OAuth callback; creates/links user server-side and issues our JWT only.
    _require_google_config()
    provider = OAuthProvider.GOOGLE

    oauth_error = request.query_params.get("error")
    if oauth_error:
        if oauth_error == "access_denied":
            log_oauth_attempt(
                provider=provider,
                outcome="failure",
                error_reason="access_denied",
            )
            return oauth_error_redirect(
                "access_denied",
                "You declined to authorize Google sign-in",
            )
        log_oauth_attempt(
            provider=provider,
            outcome="failure",
            error_reason=f"provider_error:{oauth_error}",
        )
        return oauth_error_redirect(
            "provider_error",
            "Google authorization failed",
        )

    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        log_oauth_attempt(
            provider=provider,
            outcome="failure",
            error_reason="token_exchange_failed",
        )
        return oauth_error_redirect(
            "provider_error",
            "Failed to complete Google sign-in",
        )

    try:
        profile = parse_google_profile(token)
        result = resolve_oauth_user(db, profile)
    except OAuthFlowError as exc:
        log_oauth_attempt(
            provider=provider,
            outcome="failure",
            error_reason=exc.code,
        )
        return oauth_error_redirect(exc.code, exc.message)

    access_token = create_access_token(
        result.user.id,
        result.user.email,
        result.user.is_admin,
    )
    log_oauth_attempt(
        provider=provider,
        outcome="success",
        user_id=result.user.id,
        is_new_user=result.is_new_user,
        is_email_link=result.is_email_link,
    )
    return oauth_success_redirect(access_token, is_new_user=result.is_new_user)


@router.get("/facebook/login")
async def facebook_login(request: Request) -> RedirectResponse:
    # Authz: public entry point; redirects browser to Facebook consent (state managed by Authlib).
    _require_facebook_config()
    return await oauth.facebook.authorize_redirect(request, settings.facebook_redirect_uri)


@router.get("/facebook/callback")
async def facebook_callback(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    # Authz: public OAuth callback; creates/links user server-side and issues our JWT only.
    _require_facebook_config()
    provider = OAuthProvider.FACEBOOK

    oauth_error = request.query_params.get("error")
    if oauth_error:
        if oauth_error in {"access_denied", "user_denied"}:
            log_oauth_attempt(
                provider=provider,
                outcome="failure",
                error_reason="access_denied",
            )
            return oauth_error_redirect(
                "access_denied",
                "You declined to authorize Facebook sign-in",
            )
        log_oauth_attempt(
            provider=provider,
            outcome="failure",
            error_reason=f"provider_error:{oauth_error}",
        )
        return oauth_error_redirect(
            "provider_error",
            "Facebook authorization failed",
        )

    try:
        token = await oauth.facebook.authorize_access_token(request)
    except OAuthError:
        log_oauth_attempt(
            provider=provider,
            outcome="failure",
            error_reason="token_exchange_failed",
        )
        return oauth_error_redirect(
            "provider_error",
            "Failed to complete Facebook sign-in",
        )

    try:
        response = await oauth.facebook.get(
            "me?fields=id,email",
            token=token,
        )
        response.raise_for_status()
        profile = parse_facebook_profile(response.json())
        result = resolve_oauth_user(db, profile)
    except OAuthFlowError as exc:
        log_oauth_attempt(
            provider=provider,
            outcome="failure",
            error_reason=exc.code,
        )
        return oauth_error_redirect(exc.code, exc.message)
    except OAuthError:
        log_oauth_attempt(
            provider=provider,
            outcome="failure",
            error_reason="profile_fetch_failed",
        )
        return oauth_error_redirect(
            "provider_error",
            "Failed to fetch Facebook profile",
        )

    access_token = create_access_token(
        result.user.id,
        result.user.email,
        result.user.is_admin,
    )
    log_oauth_attempt(
        provider=provider,
        outcome="success",
        user_id=result.user.id,
        is_new_user=result.is_new_user,
        is_email_link=result.is_email_link,
    )
    return oauth_success_redirect(access_token, is_new_user=result.is_new_user)
