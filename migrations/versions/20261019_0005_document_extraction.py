"""Persist local PDF extraction runs and source passages."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261019_0005"
down_revision: Union[str, None] = "20261019_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("source_file_references", sa.Column(
        "review_state", sa.String(24), server_default="active", nullable=False))
    op.create_table(
        "extraction_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("processor", sa.String(80), nullable=False),
        sa.Column("processor_version", sa.String(40), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["file_id"], ["source_files.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_extraction_runs_file_id", "extraction_runs", ["file_id"])
    op.create_table(
        "source_passages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["extraction_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["file_id"], ["source_files.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_source_passages_run_id", "source_passages", ["run_id"])
    op.create_index("ix_source_passages_file_id", "source_passages", ["file_id"])


def downgrade() -> None:
    op.drop_table("source_passages")
    op.drop_table("extraction_runs")
    op.drop_column("source_file_references", "review_state")
