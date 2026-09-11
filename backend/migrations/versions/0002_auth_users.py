"""Add authenticated citizen accounts and ticket ownership.

Revision ID: 0002_auth_users
Revises: 0001_initial
Create Date: 2026-09-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_auth_users"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"], unique=False)

    with op.batch_alter_table("tickets") as batch_op:
        batch_op.add_column(sa.Column("submitted_by_user_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_tickets_submitted_by_user_id_users",
            "users",
            ["submitted_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_tickets_submitted_by_user_id", ["submitted_by_user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("tickets") as batch_op:
        batch_op.drop_index("ix_tickets_submitted_by_user_id")
        batch_op.drop_constraint("fk_tickets_submitted_by_user_id_users", type_="foreignkey")
        batch_op.drop_column("submitted_by_user_id")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
