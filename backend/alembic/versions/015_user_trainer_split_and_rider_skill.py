"""Split is_trainer into self-reported trainer flags; add rider_skill_level.

Revision ID: 015_trainer_rider_skill
Revises: 014_user_is_trainer
Create Date: 2026-07-05
"""

from typing import Union
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "015_trainer_rider_skill"
down_revision: Union[str, None] = "014_user_is_trainer"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    op.execute("ALTER TYPE platform_flag_type ADD VALUE IF NOT EXISTS 'trainer_self_report'")

    op.add_column(
        "users",
        sa.Column(
            "is_horse_trainer",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "is_riding_instructor",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "trainer_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column("users", sa.Column("rider_skill_level", sa.SmallInteger(), nullable=True))

    op.execute(
        """
        UPDATE users
        SET is_horse_trainer = true, is_riding_instructor = true
        WHERE is_trainer = true
        """
    )

    migrated = bind.execute(
        sa.text("SELECT id FROM users WHERE is_horse_trainer = true")
    ).fetchall()
    for (user_id,) in migrated:
        bind.execute(
            sa.text(
                """
                INSERT INTO platform_flags (id, user_id, flag_type, details, created_at)
                VALUES (:id, :user_id, 'trainer_self_report', :details, now())
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "user_id": str(user_id),
                "details": '{"source": "migration_from_is_trainer"}',
            },
        )

    op.drop_column("users", "is_trainer")

    op.alter_column("users", "is_horse_trainer", server_default=None)
    op.alter_column("users", "is_riding_instructor", server_default=None)
    op.alter_column("users", "trainer_verified", server_default=None)


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_trainer",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.execute(
        """
        UPDATE users
        SET is_trainer = true
        WHERE is_horse_trainer = true OR is_riding_instructor = true
        """
    )
    op.execute(
        """
        DELETE FROM platform_flags
        WHERE flag_type = 'trainer_self_report'
          AND details->>'source' = 'migration_from_is_trainer'
        """
    )
    op.drop_column("users", "rider_skill_level")
    op.drop_column("users", "trainer_verified")
    op.drop_column("users", "is_riding_instructor")
    op.drop_column("users", "is_horse_trainer")
    op.alter_column("users", "is_trainer", server_default=None)
