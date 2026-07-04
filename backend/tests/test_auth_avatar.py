from io import BytesIO

from PIL import Image

from app.models.user import VerificationStatus
from tests.conftest import auth_header, create_user


def _fake_jpeg_bytes() -> bytes:
    image = Image.new("RGB", (20, 20), color="red")
    buf = BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()


def test_register_does_not_require_photo(client) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "newrider@example.com",
            "password": "password123",
            "first_name": "New",
            "last_name": "Rider",
        },
    )
    assert response.status_code == 201
    assert response.json()["avatar_url"] is None


def test_me_has_null_avatar_by_default(client, db_session) -> None:
    user = create_user(
        db_session,
        email="noavatar@example.com",
        verification_status=VerificationStatus.VERIFIED,
    )
    response = client.get("/auth/me", headers=auth_header(user))
    assert response.status_code == 200
    assert response.json()["avatar_url"] is None


def test_unverified_user_cannot_upload_avatar(client, db_session) -> None:
    user = create_user(
        db_session,
        email="pending-avatar@example.com",
        verification_status=VerificationStatus.PENDING,
    )
    response = client.post(
        "/auth/me/avatar",
        headers=auth_header(user),
        files={"file": ("avatar.jpg", _fake_jpeg_bytes(), "image/jpeg")},
    )
    assert response.status_code == 403


def test_verified_user_can_upload_and_fetch_avatar(client, db_session) -> None:
    user = create_user(
        db_session,
        email="avatar-owner@example.com",
        verification_status=VerificationStatus.VERIFIED,
    )
    upload_response = client.post(
        "/auth/me/avatar",
        headers=auth_header(user),
        files={"file": ("avatar.jpg", _fake_jpeg_bytes(), "image/jpeg")},
    )
    assert upload_response.status_code == 200
    body = upload_response.json()
    assert body["avatar_url"] is not None
    assert body["avatar_url"].endswith(".jpg")

    me_response = client.get("/auth/me", headers=auth_header(user))
    assert me_response.status_code == 200
    assert me_response.json()["avatar_url"] == body["avatar_url"]


def test_avatar_upload_rejects_non_image_files(client, db_session) -> None:
    user = create_user(
        db_session,
        email="bad-avatar@example.com",
        verification_status=VerificationStatus.VERIFIED,
    )
    response = client.post(
        "/auth/me/avatar",
        headers=auth_header(user),
        files={"file": ("not-an-image.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400
