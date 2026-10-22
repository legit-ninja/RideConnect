import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.db as db_module
from app.db import Base, get_db
from app.main import app as api_app
import app.models  # noqa: F401 — ensure shop/vendor tables in metadata
from app.models.species import Species
from app.models.user import User, VerificationStatus
from app.services.security import create_access_token, hash_password


@pytest.fixture(autouse=True)
def _test_jitter_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCATION_JITTER_SECRET", "test-jitter-secret")
    from app.config import settings

    settings.location_jitter_secret = "test-jitter-secret"


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    previous_engine = db_module.engine
    previous_session_factory = db_module.SessionLocal
    db_module.engine = engine
    db_module.SessionLocal = session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        db_module.engine = previous_engine
        db_module.SessionLocal = previous_session_factory


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    api_app.dependency_overrides[get_db] = override_get_db
    with TestClient(api_app) as test_client:
        yield test_client
    api_app.dependency_overrides.clear()


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
    is_horse_trainer: bool = False,
    is_riding_instructor: bool = False,
    trainer_verified: bool = False,
    rider_skill_level: int | None = None,
    is_rider: bool = True,
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED,
    is_minor: bool = False,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password("password123"),
        first_name="Test",
        last_name="User",
        is_rider=is_rider,
        is_owner=is_owner,
        is_horse_trainer=is_horse_trainer,
        is_riding_instructor=is_riding_instructor,
        trainer_verified=trainer_verified,
        rider_skill_level=rider_skill_level,
        is_admin=is_admin,
        verification_status=verification_status,
        is_minor=is_minor,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_header(user: User) -> dict[str, str]:
    token = create_access_token(user.id, user.email, user.is_admin)
    return {"Authorization": f"Bearer {token}"}
