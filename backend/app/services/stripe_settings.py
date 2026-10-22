from app.config import settings


def stripe_secret_key_configured() -> bool:
    return bool((settings.stripe_secret_key or "").strip())


def stripe_webhook_secret_configured() -> bool:
    return bool((settings.stripe_webhook_secret or "").strip())


def checkout_payments_available() -> bool:
    if stripe_secret_key_configured():
        return True
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
    secret = (settings.stripe_secret_key or "").strip()
    publishable = (settings.stripe_publishable_key or "").strip()
    if secret.startswith("sk_test_"):
        return True
    if publishable.startswith("pk_test_"):
        return True
    return False
