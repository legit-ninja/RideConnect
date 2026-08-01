from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.models.user import User
from app.models.vendor_profile import VendorProfile, VendorStatus
from app.services.security import hash_password


def ensure_admin_user() -> None:
    if not settings.admin_email or not settings.admin_password:
        return

    db: Session = SessionLocal()
    try:
        email = settings.admin_email.lower()
        admin = db.scalar(select(User).where(User.email == email))
        if admin is None:
            admin = User(
                email=email,
                password_hash=hash_password(settings.admin_password),
                is_rider=True,
                is_owner=True,
                is_admin=True,
                is_vendor=True,
            )
            db.add(admin)
            db.commit()
        elif not admin.is_admin:
            admin.is_admin = True
            db.commit()
    finally:
        db.close()


def ensure_platform_vendor_profile() -> None:
    """Ensure admin has an approved PE vendor profile for first-party catalog."""
    if not settings.admin_email:
        return
    db: Session = SessionLocal()
    try:
        email = settings.admin_email.lower()
        admin = db.scalar(select(User).where(User.email == email))
        if admin is None:
            return
        profile = db.scalar(select(VendorProfile).where(VendorProfile.user_id == admin.id))
        if profile is None:
            admin.is_vendor = True
            db.add(
                VendorProfile(
                    user_id=admin.id,
                    display_name="Phantom Equestrian",
                    status=VendorStatus.APPROVED,
                )
            )
            db.commit()
        elif profile.status != VendorStatus.APPROVED:
            profile.status = VendorStatus.APPROVED
            admin.is_vendor = True
            db.commit()
    finally:
        db.close()
