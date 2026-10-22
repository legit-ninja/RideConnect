import logging

from app.config import settings

logger = logging.getLogger(__name__)
_mismatch_logged: tuple[str, str] | None = None


def _key_mode(key: str | None, test: tuple[str, ...], live: tuple[str, ...]) -> str | None:
    key = (key or "").strip()
    return "test" if key.startswith(test) else "live" if key.startswith(live) else None


def stripe_key_modes_mismatch() -> bool:
    """True when the secret and publishable keys are for different modes (test vs live)."""
    global _mismatch_logged
    secret = _key_mode(settings.stripe_secret_key, ("sk_test_", "rk_test_"), ("sk_live_", "rk_live_"))
    publishable = _key_mode(settings.stripe_publishable_key, ("pk_test_",), ("pk_live_",))
    if secret is None or publishable is None or secret == publishable:
        return False
    if _mismatch_logged != (secret, publishable):
        logger.error(
            "Stripe config error: key mode mismatch (secret key is %s mode, publishable key is %s mode); "
            "payments are disabled until both keys use the same mode",
            secret,
            publishable,
        )
        _mismatch_logged = (secret, publishable)
    return True


def stripe_secret_key_configured() -> bool:
    return bool((settings.stripe_secret_key or "").strip())


def stripe_webhook_secret_configured() -> bool:
    return bool((settings.stripe_webhook_secret or "").strip())


def checkout_payments_available() -> bool:
    if stripe_secret_key_configured():
        return not stripe_key_modes_mismatch()
    return (
        settings.shop_dev_fake_payments
        and settings.environment != "production"
    )


def effective_stripe_secret_key() -> str | None:
    key = (settings.stripe_secret_key or "").strip()
    return key or None


def effective_stripe_webhook_secret() -> str | None:
    secret = (settings.stripe_webhook_secret or "").strip()
    return secret or None


def stripe_test_mode_active() -> bool:
    # Follows the secret key only: that is the key that actually charges.
    return (settings.stripe_secret_key or "").strip().startswith(("sk_test_", "rk_test_"))
