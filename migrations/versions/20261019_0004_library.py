"""Add project library sources and immutable file versions."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261019_0004"
down_revision: Union[str, None] = "20261019_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table("sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(500), nullable=False), sa.Column("authors", sa.Text()),
        sa.Column("year", sa.Integer()), sa.Column("doi", sa.String(255)),
        sa.Column("metadata_provenance", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "doi", name="uq_sources_project_doi"))
    op.create_index("ix_sources_project_id", "sources", ["project_id"])
    op.create_table("source_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False), sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("media_type", sa.String(100), nullable=False), sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False), sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("source_id", "version", name="uq_source_files_source_version"),
        sa.UniqueConstraint("source_id", "sha256", name="uq_source_files_source_sha256"),
        sa.UniqueConstraint("storage_key"))
    op.create_index("ix_source_files_source_id", "source_files", ["source_id"])
    op.create_table("source_file_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reference_type", sa.String(40), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["file_id"], ["source_files.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("file_id", "reference_type", "reference_id", name="uq_source_file_reference"))
    op.create_index("ix_source_file_references_file_id", "source_file_references", ["file_id"])

def downgrade() -> None:
    op.drop_table("source_file_references")
    op.drop_table("source_files")
    op.drop_table("sources")
