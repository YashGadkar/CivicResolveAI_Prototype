"""Create CivicResolve ticket and audit schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tickets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ticket_code", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("request_digest", sa.String(length=64), nullable=True),
        sa.Column("complaint", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=24), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("landmark", sa.String(length=255), nullable=True),
        sa.Column("contact", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("duration", sa.String(length=80), nullable=True),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("urgency", sa.String(length=16), nullable=False),
        sa.Column("department", sa.String(length=120), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("sla_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sla_state", sa.String(length=24), nullable=False),
        sa.Column("resolution_recommendation", sa.JSON(), nullable=False),
        sa.Column("citizen_response", sa.Text(), nullable=False),
        sa.Column("reasoning_summary", sa.Text(), nullable=False),
        sa.Column("assigned_officer", sa.String(length=120), nullable=True),
        sa.Column("duplicate_of", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tickets_ticket_code", "tickets", ["ticket_code"], unique=True)
    op.create_index("ix_tickets_idempotency_key", "tickets", ["idempotency_key"], unique=True)
    op.create_index("ix_tickets_category", "tickets", ["category"], unique=False)
    op.create_index("ix_tickets_priority", "tickets", ["priority"], unique=False)
    op.create_index("ix_tickets_department", "tickets", ["department"], unique=False)
    op.create_index("ix_tickets_status", "tickets", ["status"], unique=False)
    op.create_index("ix_tickets_category_location", "tickets", ["category", "location"], unique=False)
    op.create_index("ix_tickets_sla_status", "tickets", ["sla_state", "status"], unique=False)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ticket_id", sa.String(length=36), nullable=False),
        sa.Column("event", sa.String(length=100), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_ticket_id", "audit_events", ["ticket_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_events_ticket_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_tickets_sla_status", table_name="tickets")
    op.drop_index("ix_tickets_category_location", table_name="tickets")
    op.drop_index("ix_tickets_status", table_name="tickets")
    op.drop_index("ix_tickets_department", table_name="tickets")
    op.drop_index("ix_tickets_priority", table_name="tickets")
    op.drop_index("ix_tickets_category", table_name="tickets")
    op.drop_index("ix_tickets_idempotency_key", table_name="tickets")
    op.drop_index("ix_tickets_ticket_code", table_name="tickets")
    op.drop_table("tickets")
