"""Alembic 021 idempotency against SQLite (users.is_vendor split from 020)."""

import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text

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
    migration = _load_migration_021()
    with engine.begin() as connection:
        ctx = MigrationContext.configure(connection)
        with Operations.context(ctx):
            migration.upgrade()


def _users_table_without_vendor(engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE users (
                    id CHAR(36) PRIMARY KEY NOT NULL,
                    email VARCHAR(255) NOT NULL
                )
                """
            )
        )


def _users_table_with_vendor(engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE users (
                    id CHAR(36) PRIMARY KEY NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    is_vendor BOOLEAN NOT NULL DEFAULT 0
                )
                """
            )
        )


def test_migration_021_adds_column_when_missing(tmp_path: Path) -> None:
    """Scenario (c): post-020 users without is_vendor → 021 adds the column."""
    db_path = tmp_path / "c.db"
    engine = create_engine(f"sqlite:///{db_path}")
    _users_table_without_vendor(engine)
    _run_021_upgrade(engine)
    columns = {c["name"] for c in inspect(engine).get_columns("users")}
    assert "is_vendor" in columns


def test_migration_021_idempotent_when_column_exists(tmp_path: Path) -> None:
    """Scenario (b): prod-like 020 already has is_vendor → 021 is a no-op."""
    db_path = tmp_path / "b.db"
    engine = create_engine(f"sqlite:///{db_path}")
    _users_table_with_vendor(engine)
    _run_021_upgrade(engine)
    _run_021_upgrade(engine)
    columns = {c["name"] for c in inspect(engine).get_columns("users")}
    assert "is_vendor" in columns


def test_migration_021_fresh_install_after_020_stamp(tmp_path: Path) -> None:
    """Scenario (a): fresh DB at 020 revision shape gains is_vendor via 021 only."""
    db_path = tmp_path / "a.db"
    engine = create_engine(f"sqlite:///{db_path}")
    _users_table_without_vendor(engine)
    _run_021_upgrade(engine)
    columns = {c["name"] for c in inspect(engine).get_columns("users")}
    assert "is_vendor" in columns
