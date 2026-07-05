from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_host
from app.models.animal import Animal
from app.models.listing import Listing
from app.models.listing_availability_slot import ListingAvailabilitySlot, SlotStatus
from app.models.user import User
from app.schemas.animal import AnimalCreateRequest, AnimalResponse, AnimalUpdateRequest
from app.schemas.availability_slot import (
    AvailabilitySlotResponse,
    CreateAvailabilitySlotRequest,
    UpdateAvailabilitySlotRequest,
)
from app.schemas.listing import (
    ListingCreateRequest,
    ListingResponse,
    ListingUpdateRequest,
)
from app.services.events import log_event
from app.services.listings import get_species_by_id
from app.config import settings
from app.services.public_location import default_display_location, jitter_coordinates
from app.services.riding_styles import require_horse_riding_styles
from app.services.slug import generate_listing_slug

router = APIRouter(prefix="/owner", tags=["owner"])


def _get_owner_animal(db: Session, owner_id: UUID, animal_id: UUID) -> Animal | None:
    return db.scalar(
        select(Animal).where(Animal.id == animal_id, Animal.owner_id == owner_id)
    )


def _get_owner_listing(db: Session, owner_id: UUID, listing_id: UUID) -> Listing | None:
    return db.scalar(
        select(Listing).where(Listing.id == listing_id, Listing.owner_id == owner_id)
    )


@router.get("/animals", response_model=list[AnimalResponse])
def list_owner_animals(
    db: Session = Depends(get_db),
    host: User = Depends(require_host),
) -> list[Animal]:
    # Authz: verified host (owner or trainer) may list only their own animals.
    return list(
        db.scalars(
            select(Animal)
            .where(Animal.owner_id == host.id)
            .order_by(Animal.created_at.desc())
        ).all()
    )


@router.post("/animals", response_model=AnimalResponse, status_code=status.HTTP_201_CREATED)
def create_owner_animal(
    payload: AnimalCreateRequest,
    db: Session = Depends(get_db),
    host: User = Depends(require_host),
) -> Animal:
    # Authz: verified owner may create animals they own.
    species = get_species_by_id(db, payload.species_id)
    if species is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid species")

    riding_styles = require_horse_riding_styles(
        species, [style.value for style in payload.riding_styles]
    )

    animal = Animal(
        owner_id=host.id,
        species_id=payload.species_id,
        name=payload.name,
        breed=payload.breed,
        age=payload.age,
        description=payload.description,
        lat=payload.lat,
        lng=payload.lng,
        address=payload.address,
        photo_urls=payload.photo_urls,
        riding_styles=riding_styles,
    )
    db.add(animal)
    db.commit()
    db.refresh(animal)
    return animal


@router.get("/animals/{animal_id}", response_model=AnimalResponse)
def get_owner_animal(
    animal_id: UUID,
    db: Session = Depends(get_db),
    host: User = Depends(require_host),
) -> Animal:
    # Authz: verified owner may read only their own animal.
    animal = _get_owner_animal(db, host.id, animal_id)
    if animal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal not found")
    return animal


@router.patch("/animals/{animal_id}", response_model=AnimalResponse)
def update_owner_animal(
    animal_id: UUID,
    payload: AnimalUpdateRequest,
    db: Session = Depends(get_db),
    host: User = Depends(require_host),
) -> Animal:
    # Authz: verified owner may update only their own animal.
    animal = _get_owner_animal(db, host.id, animal_id)
    if animal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal not found")

    species = get_species_by_id(db, payload.species_id) if payload.species_id is not None else get_species_by_id(db, animal.species_id)
    if species is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid species")

    if payload.species_id is not None:
        animal.species_id = payload.species_id
    if payload.name is not None:
        animal.name = payload.name
    if payload.breed is not None:
        animal.breed = payload.breed
    if payload.age is not None:
        animal.age = payload.age
    if payload.description is not None:
        animal.description = payload.description
    if payload.lat is not None:
        animal.lat = payload.lat
    if payload.lng is not None:
        animal.lng = payload.lng
    if payload.address is not None:
        animal.address = payload.address
    if payload.photo_urls is not None:
        animal.photo_urls = payload.photo_urls
    if payload.riding_styles is not None:
        animal.riding_styles = require_horse_riding_styles(
            species, [style.value for style in payload.riding_styles]
        )
    elif species.name == "horse" and not (animal.riding_styles or []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Horses require at least one riding style (western, english, or therapy)",
        )

    db.commit()
    db.refresh(animal)
    return animal


@router.delete("/animals/{animal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_owner_animal(
    animal_id: UUID,
    db: Session = Depends(get_db),
    host: User = Depends(require_host),
) -> None:
    # Authz: verified owner may delete only their own animal.
    animal = _get_owner_animal(db, host.id, animal_id)
    if animal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal not found")
    db.delete(animal)
    db.commit()


@router.get("/listings", response_model=list[ListingResponse])
def list_owner_listings(
    db: Session = Depends(get_db),
    host: User = Depends(require_host),
) -> list[Listing]:
    # Authz: verified owner may list only their own listings (including inactive).
    return list(
        db.scalars(
            select(Listing)
            .where(Listing.owner_id == host.id)
            .order_by(Listing.created_at.desc())
        ).all()
    )


@router.post("/listings", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
def create_owner_listing(
    payload: ListingCreateRequest,
    db: Session = Depends(get_db),
    host: User = Depends(require_host),
) -> Listing:
    # Authz: verified owner may create listings for animals they own.
    animal = _get_owner_animal(db, host.id, payload.animal_id)
    if animal is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid animal")

    display_location = payload.display_location or default_display_location(animal.address)
    pub_lat, pub_lng = jitter_coordinates(
        animal.id, animal.lat, animal.lng, settings.location_jitter_secret
    )

    for _ in range(5):
        listing = Listing(
            animal_id=payload.animal_id,
            owner_id=host.id,
            activity_type=payload.activity_type,
            price=payload.price,
            availability=payload.availability,
            friend_only_allowed=payload.friend_only_allowed,
            active=payload.active,
            slug=generate_listing_slug(animal.name),
            display_location=display_location,
            public_lat=pub_lat,
            public_lng=pub_lng,
            min_rider_skill=payload.min_rider_skill,
            max_rider_weight_lbs=payload.max_rider_weight_lbs,
            helmet_required=payload.helmet_required,
            tack_provided=payload.tack_provided,
        )
        db.add(listing)
        try:
            db.commit()
            db.refresh(listing)
            return listing
        except IntegrityError:
            db.rollback()

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not generate unique listing slug",
    )


@router.get("/listings/{listing_id}", response_model=ListingResponse)
def get_owner_listing(
    listing_id: UUID,
    db: Session = Depends(get_db),
    host: User = Depends(require_host),
) -> Listing:
    # Authz: verified owner may read only their own listing.
    listing = _get_owner_listing(db, host.id, listing_id)
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    return listing


@router.patch("/listings/{listing_id}", response_model=ListingResponse)
def update_owner_listing(
    listing_id: UUID,
    payload: ListingUpdateRequest,
    db: Session = Depends(get_db),
    host: User = Depends(require_host),
) -> Listing:
    # Authz: verified owner may update only their own listing.
    listing = _get_owner_listing(db, host.id, listing_id)
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    if payload.activity_type is not None:
        listing.activity_type = payload.activity_type
    if payload.price is not None:
        listing.price = payload.price
    if payload.availability is not None:
        listing.availability = payload.availability
    if payload.friend_only_allowed is not None:
        listing.friend_only_allowed = payload.friend_only_allowed
    if payload.active is not None:
        listing.active = payload.active
    if payload.min_rider_skill is not None:
        listing.min_rider_skill = payload.min_rider_skill
    if payload.max_rider_weight_lbs is not None:
        listing.max_rider_weight_lbs = payload.max_rider_weight_lbs
    if payload.helmet_required is not None:
        listing.helmet_required = payload.helmet_required
    if payload.tack_provided is not None:
        listing.tack_provided = payload.tack_provided

    db.commit()
    db.refresh(listing)
    return listing


@router.delete("/listings/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_owner_listing(
    listing_id: UUID,
    db: Session = Depends(get_db),
    host: User = Depends(require_host),
) -> None:
    # Authz: verified owner may delete only their own listing.
    listing = _get_owner_listing(db, host.id, listing_id)
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    db.delete(listing)
    db.commit()


@router.get("/listings/{listing_id}/slots", response_model=list[AvailabilitySlotResponse])
def list_listing_slots(
    listing_id: UUID,
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
    host: User = Depends(require_host),
) -> list[ListingAvailabilitySlot]:
    # Authz: verified owner may list slots for their own listing.
    listing = _get_owner_listing(db, host.id, listing_id)
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    stmt = select(ListingAvailabilitySlot).where(
        ListingAvailabilitySlot.listing_id == listing_id
    )
    if from_date is not None:
        stmt = stmt.where(ListingAvailabilitySlot.start_at >= from_date)
    if to_date is not None:
        stmt = stmt.where(ListingAvailabilitySlot.start_at <= to_date)
    return list(
        db.scalars(stmt.order_by(ListingAvailabilitySlot.start_at.asc())).all()
    )


@router.post(
    "/listings/{listing_id}/slots",
    response_model=AvailabilitySlotResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_listing_slot(
    listing_id: UUID,
    payload: CreateAvailabilitySlotRequest,
    db: Session = Depends(get_db),
    host: User = Depends(require_host),
) -> ListingAvailabilitySlot:
    # Authz: verified owner may create slots for their own listing.
    listing = _get_owner_listing(db, host.id, listing_id)
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    if payload.start_at <= datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot start must be in the future",
        )

    slot = ListingAvailabilitySlot(
        listing_id=listing.id,
        start_at=payload.start_at,
        end_at=payload.end_at,
        capacity=payload.capacity,
        status=SlotStatus.OPEN,
    )
    db.add(slot)
    db.flush()
    log_event(
        db,
        "slot_created",
        user_id=host.id,
        payload={"slot_id": str(slot.id), "listing_id": str(listing.id)},
    )
    db.commit()
    db.refresh(slot)
    return slot


@router.patch(
    "/listings/{listing_id}/slots/{slot_id}",
    response_model=AvailabilitySlotResponse,
)
def update_listing_slot(
    listing_id: UUID,
    slot_id: UUID,
    payload: UpdateAvailabilitySlotRequest,
    db: Session = Depends(get_db),
    host: User = Depends(require_host),
) -> ListingAvailabilitySlot:
    # Authz: verified owner may update open/blocked slots on their listing.
    listing = _get_owner_listing(db, host.id, listing_id)
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    slot = db.scalar(
        select(ListingAvailabilitySlot).where(
            ListingAvailabilitySlot.id == slot_id,
            ListingAvailabilitySlot.listing_id == listing_id,
        )
    )
    if slot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
    if slot.status in (SlotStatus.HELD, SlotStatus.BOOKED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify a held or booked slot",
        )

    if payload.start_at is not None:
        slot.start_at = payload.start_at
    if payload.end_at is not None:
        slot.end_at = payload.end_at
    if payload.status is not None:
        slot.status = SlotStatus(payload.status)

    log_event(
        db,
        "slot_updated",
        user_id=host.id,
        payload={"slot_id": str(slot.id), "listing_id": str(listing.id)},
    )
    db.commit()
    db.refresh(slot)
    return slot


@router.delete(
    "/listings/{listing_id}/slots/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_listing_slot(
    listing_id: UUID,
    slot_id: UUID,
    db: Session = Depends(get_db),
    host: User = Depends(require_host),
) -> None:
    # Authz: verified owner may delete open/blocked slots on their listing.
    listing = _get_owner_listing(db, host.id, listing_id)
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    slot = db.scalar(
        select(ListingAvailabilitySlot).where(
            ListingAvailabilitySlot.id == slot_id,
            ListingAvailabilitySlot.listing_id == listing_id,
        )
    )
    if slot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
    if slot.status == SlotStatus.BOOKED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a booked slot",
        )

    log_event(
        db,
        "slot_deleted",
        user_id=host.id,
        payload={"slot_id": str(slot.id), "listing_id": str(listing.id)},
    )
    db.delete(slot)
    db.commit()
