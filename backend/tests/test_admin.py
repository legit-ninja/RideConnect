from app.models.user import User, VerificationStatus
from app.services.security import create_access_token, hash_password
from tests.helpers import seed_test_listing


def test_non_admin_forbidden_on_stats(client, db_session) -> None:
    from tests.conftest import auth_header, create_user

    regular_user = create_user(db_session, email="user@example.com")
    response = client.get("/admin/stats", headers=auth_header(regular_user))
    assert response.status_code == 403


def test_non_admin_forbidden_on_list_users(client, db_session) -> None:
    from tests.conftest import auth_header, create_user

    regular_user = create_user(db_session, email="user2@example.com")
    response = client.get("/admin/users", headers=auth_header(regular_user))
    assert response.status_code == 403


def test_admin_list_users_paginated(client, db_session) -> None:
    from tests.conftest import auth_header, create_user

    admin_user = create_user(
        db_session,
        email="admin@example.com",
        is_admin=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    create_user(db_session, email="alpha@example.com")
    create_user(db_session, email="beta@example.com")

    response = client.get(
        "/admin/users?limit=1&offset=0", headers=auth_header(admin_user)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert len(data["items"]) == 1


def test_admin_list_users_with_local_domain_email(client, db_session) -> None:
    from tests.conftest import auth_header, create_user

    admin_user = create_user(
        db_session,
        email="admin@example.com",
        is_admin=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    create_user(
        db_session,
        email="admin@rideconnect.local",
        is_admin=True,
        verification_status=VerificationStatus.UNVERIFIED,
    )

    response = client.get("/admin/users", headers=auth_header(admin_user))
    assert response.status_code == 200
    emails = {item["email"] for item in response.json()["items"]}
    assert "admin@rideconnect.local" in emails


def test_admin_update_verification_creates_audit_log(client, db_session) -> None:
    from sqlalchemy import select

    from app.models.admin_audit_log import AdminAuditAction, AdminAuditLog
    from tests.conftest import auth_header, create_user

    admin_user = create_user(
        db_session,
        email="admin2@example.com",
        is_admin=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    regular_user = create_user(db_session, email="regular@example.com")

    response = client.patch(
        f"/admin/users/{regular_user.id}/verification",
        headers=auth_header(admin_user),
        json={"verification_status": "verified", "note": "Manual KYC approved"},
    )
    assert response.status_code == 200
    assert response.json()["verification_status"] == "verified"

    db_session.refresh(regular_user)
    assert regular_user.verification_status == VerificationStatus.VERIFIED

    audit = db_session.scalar(
        select(AdminAuditLog).where(AdminAuditLog.target_user_id == regular_user.id)
    )
    assert audit is not None
    assert audit.action == AdminAuditAction.VERIFICATION_STATUS_CHANGED


def test_admin_get_user_not_found(client, db_session) -> None:
    import uuid

    from tests.conftest import auth_header, create_user

    admin_user = create_user(
        db_session,
        email="admin3@example.com",
        is_admin=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    missing_id = uuid.uuid4()
    response = client.get(f"/admin/users/{missing_id}", headers=auth_header(admin_user))
    assert response.status_code == 404


def test_admin_user_detail_includes_marketplace_counts(
    client, db_session, horse_species
) -> None:
    from tests.conftest import auth_header, create_user

    admin_user = create_user(
        db_session,
        email="admin4@example.com",
        is_admin=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    owner = create_user(
        db_session,
        email="owner-counts@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    seed_test_listing(db_session, horse_species=horse_species, owner=owner, active=True)

    response = client.get(f"/admin/users/{owner.id}", headers=auth_header(admin_user))
    assert response.status_code == 200
    data = response.json()
    assert data["animal_count"] == 1
    assert data["listing_count"] == 1
    assert data["active_listing_count"] == 1


def test_admin_listings_filter_by_owner_id(client, db_session, horse_species) -> None:
    from tests.conftest import auth_header, create_user

    admin_user = create_user(
        db_session,
        email="admin5@example.com",
        is_admin=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    owner_a = create_user(
        db_session,
        email="owner-a@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    owner_b = create_user(
        db_session,
        email="owner-b@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    seed_test_listing(
        db_session,
        horse_species=horse_species,
        owner=owner_a,
        animal_name="Animal A",
        active=True,
    )
    seed_test_listing(
        db_session,
        horse_species=horse_species,
        owner=owner_b,
        animal_name="Animal B",
        active=True,
    )

    response = client.get(
        f"/admin/listings?owner_id={owner_a.id}",
        headers=auth_header(admin_user),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["owner_email"] == "owner-a@example.com"


def test_admin_audit_log_list(client, db_session) -> None:
    from tests.conftest import auth_header, create_user

    admin_user = create_user(
        db_session,
        email="admin6@example.com",
        is_admin=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    regular_user = create_user(db_session, email="audit-target@example.com")

    client.patch(
        f"/admin/users/{regular_user.id}/verification",
        headers=auth_header(admin_user),
        json={"verification_status": "verified", "note": "Test note"},
    )

    response = client.get("/admin/audit", headers=auth_header(admin_user))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(
        item["action"] == "verification_status_changed"
        for item in data["items"]
    )


def test_non_admin_forbidden_on_audit(client, db_session) -> None:
    from tests.conftest import auth_header, create_user

    regular_user = create_user(db_session, email="user-audit@example.com")
    response = client.get("/admin/audit", headers=auth_header(regular_user))
    assert response.status_code == 403
