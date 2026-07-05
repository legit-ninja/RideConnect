from app.models.user import VerificationStatus
from tests.helpers import seed_test_listing


def _horse_payload(species_id: str, *, riding_styles: list[str]) -> dict:
    return {
        "species_id": species_id,
        "name": "Style Test Horse",
        "lat": 36.2,
        "lng": -81.6,
        "address": "Boone, NC",
        "photo_urls": [],
        "riding_styles": riding_styles,
    }


def test_horse_create_without_riding_styles_returns_400(
    client, db_session, horse_species
) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="styles.owner@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    response = client.post(
        "/owner/animals",
        headers=auth_header(owner),
        json=_horse_payload(str(horse_species.id), riding_styles=[]),
    )
    assert response.status_code == 400
    assert "riding style" in response.json()["detail"].lower()


def test_horse_create_with_multiple_riding_styles(
    client, db_session, horse_species
) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="multi.styles@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    response = client.post(
        "/owner/animals",
        headers=auth_header(owner),
        json=_horse_payload(
            str(horse_species.id),
            riding_styles=["western", "english", "therapy"],
        ),
    )
    assert response.status_code == 201
    assert set(response.json()["riding_styles"]) == {"western", "english", "therapy"}


def test_browse_filter_by_riding_style(
    client, db_session, horse_species
) -> None:
    from tests.conftest import create_user

    owner = create_user(
        db_session,
        email="filter.owner@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )

    western_listing = seed_test_listing(
        db_session,
        horse_species=horse_species,
        owner=owner,
        animal_name="WesternStar",
    )
    western_listing.animal.riding_styles = ["western"]
    db_session.commit()

    english_listing = seed_test_listing(
        db_session,
        horse_species=horse_species,
        owner=owner,
        animal_name="EnglishStar",
    )
    english_listing.animal.riding_styles = ["english"]
    db_session.commit()

    response = client.get("/listings", params={"riding_style": "western"})
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert str(western_listing.id) in ids
    assert str(english_listing.id) not in ids
