"""add civic platform workflow tables

Revision ID: 0003_platform_workflows
Revises: 0002_auth_users
Create Date: 2026-09-11
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_platform_workflows"
down_revision = "0002_auth_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ticket_meta",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ticket_id", sa.String(length=36), nullable=False),
        sa.Column("ward", sa.String(length=120), nullable=True),
        sa.Column("zone", sa.String(length=120), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("emergency", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("incident_key", sa.String(length=128), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("citizen_confirmation", sa.String(length=24), nullable=False, server_default="PENDING"),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_id"),
    )
    op.create_index("ix_ticket_meta_ticket_id", "ticket_meta", ["ticket_id"], unique=True)
    op.create_index("ix_ticket_meta_ward", "ticket_meta", ["ward"], unique=False)
    op.create_index("ix_ticket_meta_zone", "ticket_meta", ["zone"], unique=False)
    op.create_index("ix_ticket_meta_city", "ticket_meta", ["city"], unique=False)
    op.create_index("ix_ticket_meta_emergency", "ticket_meta", ["emergency"], unique=False)
    op.create_index("ix_ticket_meta_incident_key", "ticket_meta", ["incident_key"], unique=False)
    op.create_index("ix_ticket_meta_archived_at", "ticket_meta", ["archived_at"], unique=False)

    op.create_table(
        "attachments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ticket_id", sa.String(length=36), nullable=False),
        sa.Column("uploaded_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("stored_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_name"),
    )
    op.create_index("ix_attachments_ticket_id", "attachments", ["ticket_id"], unique=False)
    op.create_index("ix_attachments_uploaded_by_user_id", "attachments", ["uploaded_by_user_id"], unique=False)
    op.create_index("ix_attachments_kind", "attachments", ["kind"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_attachments_kind", table_name="attachments")
    op.drop_index("ix_attachments_uploaded_by_user_id", table_name="attachments")
    op.drop_index("ix_attachments_ticket_id", table_name="attachments")
    op.drop_table("attachments")
    op.drop_index("ix_ticket_meta_archived_at", table_name="ticket_meta")
    op.drop_index("ix_ticket_meta_incident_key", table_name="ticket_meta")
    op.drop_index("ix_ticket_meta_emergency", table_name="ticket_meta")
    op.drop_index("ix_ticket_meta_city", table_name="ticket_meta")
    op.drop_index("ix_ticket_meta_zone", table_name="ticket_meta")
    op.drop_index("ix_ticket_meta_ward", table_name="ticket_meta")
    op.drop_index("ix_ticket_meta_ticket_id", table_name="ticket_meta")
    op.drop_table("ticket_meta")
