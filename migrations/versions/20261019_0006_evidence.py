"""Add versioned claims, evidence links and owner review decisions."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261019_0006"
down_revision: Union[str, None] = "20261019_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("manuscript_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("manuscripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("block_position", sa.Integer(), nullable=False), sa.Column("text", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False), sa.Column("manuscript_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_claims_manuscript_id", "claims", ["manuscript_id"])
    op.create_table("evidence_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("claims.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_version", sa.Integer(), nullable=False),
        sa.Column("passage_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("source_passages.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("passage_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("source_files.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("relation", sa.String(24), nullable=False), sa.Column("rationale", sa.Text()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("review_state", sa.String(24), nullable=False), sa.Column("manuscript_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_evidence_links_claim_id", "evidence_links", ["claim_id"])
    op.create_index("ix_evidence_links_passage_id", "evidence_links", ["passage_id"])
    op.create_table("review_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("evidence_link_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evidence_links.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("link_version", sa.Integer(), nullable=False), sa.Column("decision", sa.String(24), nullable=False),
        sa.Column("note", sa.Text()), sa.Column("decided_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_review_decisions_evidence_link_id", "review_decisions", ["evidence_link_id"])


def downgrade() -> None:
    op.drop_table("review_decisions")
    op.drop_table("evidence_links")
    op.drop_table("claims")
