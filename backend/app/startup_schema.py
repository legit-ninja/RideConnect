import logging

from sqlalchemy import inspect

logger = logging.getLogger(__name__)


def assert_database_schema_ready() -> None:
    """Fail fast when shop/vendor migrations have not been applied."""
    from app.db import engine

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "vendor_profiles" not in tables:
        message = (
            "Database schema missing table vendor_profiles; run alembic upgrade head"
        )
        logger.error(message)
        raise RuntimeError(message)
    if "users" not in tables:
        message = "Database schema missing table users; run alembic upgrade head"
        logger.error(message)
        raise RuntimeError(message)
    user_columns = {col["name"] for col in inspector.get_columns("users")}
    if "is_vendor" not in user_columns:
        message = (
            "Database schema missing column users.is_vendor; run alembic upgrade head"
        )
        logger.error(message)
        raise RuntimeError(message)
