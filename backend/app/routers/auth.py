import uuid
from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user, require_verified
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.events import log_event
from app.services.security import create_access_token, hash_password, verify_password
from app.services.storage import get_public_url, put_object

router = APIRouter(prefix="/auth", tags=["auth"])

# Cap stored avatar dimensions; avatars are small UI elements, not full photos.
_AVATAR_MAX_DIMENSION = 512


def _to_user_response(user: User) -> UserResponse:
    # avatar_url is derived, never stored/serialized directly from the storage key.
    avatar_url = (
        get_public_url(user.profile_photo_storage_key)
        if user.profile_photo_storage_key
        else None
    )
    return UserResponse.model_validate(user).model_copy(update={"avatar_url": avatar_url})


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
    src: str | None = Query(default=None),
    ref: str | None = Query(default=None),
) -> UserResponse:
    # Registration never requires a profile photo; profile_photo_storage_key stays
    # null until the user optionally uploads one via POST /auth/me/avatar.
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        is_rider=payload.is_rider,
        is_owner=payload.is_owner,
        is_trainer=payload.is_trainer,
        is_admin=False,
    )
    db.add(user)
    db.flush()
    log_event(
        db,
        "signup_started",
        user_id=user.id,
        src=src,
        listing_slug=ref if src == "public_listing" else None,
        invite_token=ref if src == "invite" else None,
    )
    db.commit()
    db.refresh(user)
    return _to_user_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if (
        user is None
        or user.password_hash is None
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user.id, user.email, user.is_admin)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    # Authz: bearer token must map to an existing user; any authenticated user may read self.
    return _to_user_response(current_user)


@router.post("/me/avatar", response_model=UserResponse)
async def upload_my_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified),
) -> UserResponse:
    # Authz: identity comes from the bearer token (require_verified), not the
    # request body/path, so a user can only ever replace their own avatar. Requires
    # verification so unverified/unmoderated accounts can't upload arbitrary images.
    raw = await file.read()
    try:
        image = Image.open(BytesIO(raw))
        image.load()
    except UnidentifiedImageError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid image",
        ) from None

    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    image.thumbnail((_AVATAR_MAX_DIMENSION, _AVATAR_MAX_DIMENSION))

    # Strip EXIF (same as listing photo upload) — avatars can otherwise leak GPS
    # metadata or other PII embedded in the original photo.
    buf = BytesIO()
    image.save(buf, format="JPEG", exif=b"")
    storage_key = f"avatars/{current_user.id}/{uuid.uuid4()}.jpg"
    put_object(storage_key, buf.getvalue())

    current_user.profile_photo_storage_key = storage_key
    db.commit()
    db.refresh(current_user)
    return _to_user_response(current_user)
