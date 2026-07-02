from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_owner
from app.models.animal import Animal
from app.models.listing import Listing
from app.models.user import User
from app.schemas.animal import AnimalCreateRequest, AnimalResponse, AnimalUpdateRequest
from app.schemas.listing import (
    ListingCreateRequest,
    ListingResponse,
    ListingUpdateRequest,
)
from app.services.listings import get_species_by_id

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
    owner: User = Depends(require_owner),
) -> list[Animal]:
    # Authz: verified owner may list only their own animals.
    return list(
        db.scalars(
            select(Animal)
            .where(Animal.owner_id == owner.id)
            .order_by(Animal.created_at.desc())
        ).all()
    )


@router.post("/animals", response_model=AnimalResponse, status_code=status.HTTP_201_CREATED)
def create_owner_animal(
    payload: AnimalCreateRequest,
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> Animal:
    # Authz: verified owner may create animals they own.
    species = get_species_by_id(db, payload.species_id)
    if species is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid species")

    animal = Animal(
        owner_id=owner.id,
        species_id=payload.species_id,
        name=payload.name,
        breed=payload.breed,
        age=payload.age,
        description=payload.description,
        lat=payload.lat,
        lng=payload.lng,
        address=payload.address,
        photo_urls=payload.photo_urls,
    )
    db.add(animal)
    db.commit()
    db.refresh(animal)
    return animal


@router.get("/animals/{animal_id}", response_model=AnimalResponse)
def get_owner_animal(
    animal_id: UUID,
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> Animal:
    # Authz: verified owner may read only their own animal.
    animal = _get_owner_animal(db, owner.id, animal_id)
    if animal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal not found")
    return animal


@router.patch("/animals/{animal_id}", response_model=AnimalResponse)
def update_owner_animal(
    animal_id: UUID,
    payload: AnimalUpdateRequest,
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> Animal:
    # Authz: verified owner may update only their own animal.
    animal = _get_owner_animal(db, owner.id, animal_id)
    if animal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal not found")

    if payload.species_id is not None:
        species = get_species_by_id(db, payload.species_id)
        if species is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid species")
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

    db.commit()
    db.refresh(animal)
    return animal


@router.delete("/animals/{animal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_owner_animal(
    animal_id: UUID,
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> None:
    # Authz: verified owner may delete only their own animal.
    animal = _get_owner_animal(db, owner.id, animal_id)
    if animal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal not found")
    db.delete(animal)
    db.commit()


@router.get("/listings", response_model=list[ListingResponse])
def list_owner_listings(
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> list[Listing]:
    # Authz: verified owner may list only their own listings (including inactive).
    return list(
        db.scalars(
            select(Listing)
            .where(Listing.owner_id == owner.id)
            .order_by(Listing.created_at.desc())
        ).all()
    )


@router.post("/listings", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
def create_owner_listing(
    payload: ListingCreateRequest,
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> Listing:
    # Authz: verified owner may create listings for animals they own.
    animal = _get_owner_animal(db, owner.id, payload.animal_id)
    if animal is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid animal")

    listing = Listing(
        animal_id=payload.animal_id,
        owner_id=owner.id,
        activity_type=payload.activity_type,
        price=payload.price,
        availability=payload.availability,
        friend_only_allowed=payload.friend_only_allowed,
        active=payload.active,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


@router.get("/listings/{listing_id}", response_model=ListingResponse)
def get_owner_listing(
    listing_id: UUID,
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> Listing:
    # Authz: verified owner may read only their own listing.
    listing = _get_owner_listing(db, owner.id, listing_id)
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    return listing


@router.patch("/listings/{listing_id}", response_model=ListingResponse)
def update_owner_listing(
    listing_id: UUID,
    payload: ListingUpdateRequest,
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> Listing:
    # Authz: verified owner may update only their own listing.
    listing = _get_owner_listing(db, owner.id, listing_id)
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

    db.commit()
    db.refresh(listing)
    return listing


@router.delete("/listings/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_owner_listing(
    listing_id: UUID,
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> None:
    # Authz: verified owner may delete only their own listing.
    listing = _get_owner_listing(db, owner.id, listing_id)
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    db.delete(listing)
    db.commit()
