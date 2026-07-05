from app.models.user import VerificationStatus


def test_unverified_owner_cannot_create_animal(
    client, db_session, horse_species
) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="pending@example.com",
        is_owner=True,
        verification_status=VerificationStatus.PENDING,
    )
    response = client.post(
        "/owner/animals",
        headers=auth_header(owner),
        json={
            "species_id": str(horse_species.id),
            "name": "New Horse",
            "lat": 36.2,
            "lng": -81.6,
            "address": "Boone, NC",
            "photo_urls": [],
            "riding_styles": ["western"],
        },
    )
    assert response.status_code == 403


def test_verified_owner_can_create_animal(
    client, db_session, horse_species
) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="verified@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    response = client.post(
        "/owner/animals",
        headers=auth_header(owner),
        json={
            "species_id": str(horse_species.id),
            "name": "New Horse",
            "lat": 36.2,
            "lng": -81.6,
            "address": "Boone, NC",
            "photo_urls": [],
            "riding_styles": ["western"],
        },
    )
    assert response.status_code == 201
    assert response.json()["name"] == "New Horse"
