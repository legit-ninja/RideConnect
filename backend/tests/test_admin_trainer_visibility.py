from app.models.user import VerificationStatus
from tests.conftest import auth_header, create_user


def test_admin_stats_and_user_list_include_trainer_counts(
    client, db_session
) -> None:
    admin_user = create_user(
        db_session,
        email="admin-trainer@example.com",
        is_admin=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    create_user(
        db_session,
        email="trainer-persona@example.com",
        is_owner=True,
        is_rider=False,
        is_horse_trainer=True,
        is_riding_instructor=True,
        trainer_verified=True,
        verification_status=VerificationStatus.VERIFIED,
    )

    stats_response = client.get("/admin/stats", headers=auth_header(admin_user))
    assert stats_response.status_code == 200
    stats = stats_response.json()

    users_response = client.get("/admin/users", headers=auth_header(admin_user))
    assert users_response.status_code == 200
    trainer_row = next(
        item
        for item in users_response.json()["items"]
        if item["email"] == "trainer-persona@example.com"
    )

    assert trainer_row["is_horse_trainer"] is True
    assert trainer_row["is_riding_instructor"] is True
    assert trainer_row["trainer_verified"] is True
    assert trainer_row["is_owner"] is True
    assert trainer_row["is_rider"] is False
    assert stats["trainer_users"] >= 1
    assert stats["verified_trainer_users"] >= 1
