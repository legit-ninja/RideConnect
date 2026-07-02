"""admin audit log table

Revision ID: 003_admin_audit_log
Revises: 002_oauth_accounts
Create Date: 2026-07-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_admin_audit_log"
down_revision: Union[str, None] = "002_oauth_accounts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

admin_audit_action = postgresql.ENUM(
    "verification_status_changed",
    "user_roles_changed",
    name="admin_audit_action",
    create_type=True,
)


def upgrade() -> None:
    bind = op.get_bind()
    admin_audit_action.create(bind, checkfirst=True)

    op.create_table(
        "admin_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "action",
            postgresql.ENUM(
                "verification_status_changed",
                "user_roles_changed",
                name="admin_audit_action",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("target_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_audit_log_actor_id", "admin_audit_log", ["actor_id"])
    op.create_index(
        "ix_admin_audit_log_target_user_id", "admin_audit_log", ["target_user_id"]
    )
    op.create_index("ix_admin_audit_log_created_at", "admin_audit_log", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_admin_audit_log_created_at", table_name="admin_audit_log")
    op.drop_index("ix_admin_audit_log_target_user_id", table_name="admin_audit_log")
    op.drop_index("ix_admin_audit_log_actor_id", table_name="admin_audit_log")
    op.drop_table("admin_audit_log")
    admin_audit_action.drop(op.get_bind(), checkfirst=True)
