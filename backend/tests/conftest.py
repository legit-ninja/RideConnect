import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models.species import Species
from app.models.user import User, VerificationStatus
from app.services.security import create_access_token, hash_password


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def horse_species(db_session: Session) -> Species:
    species = Species(name="horse", active_in_ui=True)
    db_session.add(species)
    db_session.commit()
    db_session.refresh(species)
    return species


def create_user(
    db: Session,
    *,
    email: str,
    is_admin: bool = False,
    is_owner: bool = False,
    is_rider: bool = True,
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password("password123"),
        first_name="Test",
        last_name="User",
        is_rider=is_rider,
        is_owner=is_owner,
        is_admin=is_admin,
        verification_status=verification_status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_header(user: User) -> dict[str, str]:
    token = create_access_token(user.id, user.email, user.is_admin)
    return {"Authorization": f"Bearer {token}"}
