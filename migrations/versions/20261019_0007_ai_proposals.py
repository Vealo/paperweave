"""Add owner-scoped, idempotent manuscript AI proposals."""
from typing import Sequence, Union
from sqlalchemy import table, column
from alembic import op
from uuid import uuid4
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261019_0007"
down_revision: Union[str, None] = "20261019_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "manuscript_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("manuscript_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("manuscripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("manuscript_id", "version", name="uq_manuscript_revisions_manuscript_version"),
    )
    op.create_index("ix_manuscript_revisions_manuscript_id", "manuscript_revisions", ["manuscript_id"])
    connection = op.get_bind()
    existing = connection.execute(sa.text("SELECT id, version, content, updated_at FROM manuscripts")).mappings().all()
    revision_rows = table(
        "manuscript_revisions",
        column("id", postgresql.UUID(as_uuid=True)),
        column("manuscript_id", postgresql.UUID(as_uuid=True)),
        column("version", sa.Integer()),
        column("content", postgresql.JSONB(astext_type=sa.Text())),
        column("created_at", sa.DateTime(timezone=True)),
    )
    if existing:
        connection.execute(revision_rows.insert(), [
            {"id": uuid4(), "manuscript_id": row["id"], "version": row["version"],
             "content": row["content"], "created_at": row["updated_at"]}
            for row in existing
        ])
    op.create_table(
        "ai_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("manuscript_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("manuscripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("target_version", sa.Integer(), nullable=False),
        sa.Column("target_position", sa.Integer(), nullable=False),
        sa.Column("context_manifest", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("suggestion", sa.Text()),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("decision_at", sa.DateTime(timezone=True)),
        sa.Column("decision_note", sa.Text()),
        sa.Column("error_code", sa.String(80)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "idempotency_key", name="uq_ai_proposals_project_idempotency"),
    )
    op.create_index("ix_ai_proposals_project_id", "ai_proposals", ["project_id"])
    op.create_index("ix_ai_proposals_manuscript_id", "ai_proposals", ["manuscript_id"])


def downgrade() -> None:
    op.drop_table("ai_proposals")
    op.drop_table("manuscript_revisions")
