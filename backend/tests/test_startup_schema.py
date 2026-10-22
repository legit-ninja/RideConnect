import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import app.db as db_module
import app.models  # noqa: F401 — register metadata
from app.config import settings
from app.db import Base
from app.main import app

_MIGRATION_021 = (
    Path(__file__).resolve().parents[1] / "alembic" / "versions" / "021_users_is_vendor.py"
)


def _load_migration_021():
    spec = importlib.util.spec_from_file_location("migration_021", _MIGRATION_021)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _run_021_upgrade(engine) -> None:
    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    migration = _load_migration_021()
    with engine.begin() as connection:
        ctx = MigrationContext.configure(connection)
        with Operations.context(ctx):
            migration.upgrade()


@pytest.fixture(autouse=True)
def _restore_app_database() -> None:
    old_engine = db_module.engine
    old_session_factory = db_module.SessionLocal
    old_url = settings.database_url
    yield
    db_module.engine = old_engine
    db_module.SessionLocal = old_session_factory
    settings.database_url = old_url


def _rebind_app_database(db_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", url)
    settings.database_url = url
    settings.admin_email = ""
    settings.admin_password = ""
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
    )
    db_module.engine = engine
    db_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _drop_users_is_vendor(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users DROP COLUMN is_vendor"))


def test_startup_fails_when_is_vendor_column_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "missing_is_vendor.db"
    _rebind_app_database(db_path, monkeypatch)
    Base.metadata.create_all(bind=db_module.engine)
    _drop_users_is_vendor(db_module.engine)

    with pytest.raises(RuntimeError, match="users.is_vendor"):
        with TestClient(app):
            pass


def test_app_boots_after_021_adds_is_vendor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "post_021.db"
    _rebind_app_database(db_path, monkeypatch)
    Base.metadata.create_all(bind=db_module.engine)
    _drop_users_is_vendor(db_module.engine)
    _run_021_upgrade(db_module.engine)

    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        from tests.conftest import auth_header, create_user

        session = db_module.SessionLocal()
        try:
            user = create_user(session, email="boot-user@test.com")
        finally:
            session.close()
        me = client.get("/auth/me", headers=auth_header(user))
        assert me.status_code == 200
        assert me.json()["email"] == "boot-user@test.com"


def test_app_boots_when_is_vendor_already_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "prod_like.db"
    _rebind_app_database(db_path, monkeypatch)
    Base.metadata.create_all(bind=db_module.engine)
    _run_021_upgrade(db_module.engine)
    _run_021_upgrade(db_module.engine)

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
