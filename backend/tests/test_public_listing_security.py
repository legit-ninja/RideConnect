import json

from app.models.user import VerificationStatus
from tests.helpers import seed_test_listing

FORBIDDEN_KEYS = {
    "address",
    "lat",
    "lng",
    "description",
    "owner_id",
    "animal_id",
    "owner_email",
    "owner_last_name",
    "email",
    "phone",
}


def test_public_listing_does_not_leak_private_fields(
    client, db_session, horse_species
) -> None:
    from tests.conftest import create_user

    owner = create_user(
        db_session,
        email="secret.owner@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
        is_rider=False,
    )
    owner.last_name = "Secretlastname"
    db_session.commit()

    listing = seed_test_listing(
        db_session,
        horse_species=horse_species,
        owner=owner,
        animal_name="Midnight",
        address="123 Hidden Farm Rd, Boone, NC 28607",
        lat=36.2168,
        lng=-81.6746,
    )
    animal = listing.animal
    animal.description = "Private barn notes with gate code"
    db_session.commit()

    response = client.get(f"/public/listings/{listing.slug}")
    assert response.status_code == 200
    payload = response.json()
    serialized = json.dumps(payload).lower()

    for key in FORBIDDEN_KEYS:
        assert key not in payload, f"forbidden key leaked: {key}"

    assert "123 hidden farm" not in serialized
    assert "secret.owner@example.com" not in serialized
    assert "secretlastname" not in serialized
    assert payload["owner_first_name"] == "Test"
    assert payload["owner_last_initial"] == "S"
    assert payload["display_location"] != animal.address
    assert payload["public_lat"] != animal.lat or payload["public_lng"] != animal.lng
