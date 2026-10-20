"""Add PostgreSQL catalog and lifecycle metadata for user files."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261020_0010"
down_revision: Union[str, None] = "20261020_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "file_artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("domain_type", sa.String(40)),
        sa.Column("domain_id", postgresql.UUID(as_uuid=True)),
        sa.Column("domain_parent_id", postgresql.UUID(as_uuid=True)),
        sa.Column("backend", sa.String(16), nullable=False),
        sa.Column("bucket", sa.String(128), nullable=False, server_default=""),
        sa.Column("object_key", sa.String(512), nullable=False),
        sa.Column("original_name", sa.String(255)),
        sa.Column("media_type", sa.String(120), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("lifecycle", sa.String(24), nullable=False, server_default="active"),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("cleanup_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_cleanup_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("kind IN ('avatar', 'image', 'document')", name="ck_file_artifacts_kind"),
        sa.CheckConstraint("lifecycle IN ('pending_upload', 'active', 'pending_delete', 'deleted', 'failed')", name="ck_file_artifacts_lifecycle"),
        sa.UniqueConstraint("backend", "bucket", "object_key", name="uq_file_artifacts_backend_object"),
        sa.UniqueConstraint("owner_user_id", "idempotency_key", name="uq_file_artifacts_owner_idempotency"),
    )
    op.create_index("ix_file_artifacts_owner_user_id", "file_artifacts", ["owner_user_id"])
    op.create_index("ix_file_artifacts_domain_id", "file_artifacts", ["domain_id"])
    op.create_index("ix_file_artifacts_domain_parent_id", "file_artifacts", ["domain_parent_id"])
    op.create_index("ix_file_artifacts_lifecycle", "file_artifacts", ["lifecycle"])
    op.add_column("users", sa.Column("avatar_artifact_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_users_avatar_artifact", "users", "file_artifacts", ["avatar_artifact_id"], ["id"], ondelete="SET NULL")
    op.add_column("source_files", sa.Column("artifact_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_source_files_artifact", "source_files", "file_artifacts", ["artifact_id"], ["id"], ondelete="RESTRICT")
    op.create_unique_constraint("uq_source_files_artifact_id", "source_files", ["artifact_id"])

    # Preserve existing locally stored source files and their IDs, versions, hashes and links.
    op.execute(sa.text("""
        INSERT INTO file_artifacts (
            id, owner_user_id, kind, domain_type, domain_id, domain_parent_id, backend, bucket, object_key,
            original_name, media_type, size_bytes, checksum_sha256, version, lifecycle, idempotency_key
        )
        SELECT sf.id, p.owner_id, 'document', 'source_file', sf.id, sf.source_id, 'local', '', sf.storage_key,
               sf.original_name, sf.media_type, sf.size_bytes, sf.sha256, sf.version, 'active',
               'legacy-source-' || sf.id::text
        FROM source_files sf JOIN sources s ON s.id = sf.source_id JOIN projects p ON p.id = s.project_id
    """))
    op.execute(sa.text("UPDATE source_files SET artifact_id = id"))

    # Legacy avatar metadata did not include size/checksum; retain the file and key, marking those
    # two values as unavailable until the object is replaced through the validated upload path.
    op.execute(sa.text("""
        INSERT INTO file_artifacts (
            id, owner_user_id, kind, domain_type, domain_id, backend, bucket, object_key,
            original_name, media_type, size_bytes, checksum_sha256, version, lifecycle, idempotency_key
        )
        SELECT gen_random_uuid(), id, 'avatar', 'user', id, 'local', '', avatar_key,
               'legacy-avatar', avatar_media_type, 0, repeat('0', 64), 1, 'active',
               'legacy-avatar-' || id::text
        FROM users WHERE avatar_key IS NOT NULL
    """))
    op.execute(sa.text("""
        UPDATE users u SET avatar_artifact_id = a.id
        FROM file_artifacts a WHERE a.owner_user_id = u.id AND a.kind = 'avatar' AND a.domain_id = u.id
          AND a.idempotency_key = 'legacy-avatar-' || u.id::text
    """))


def downgrade() -> None:
    op.drop_constraint("uq_source_files_artifact_id", "source_files", type_="unique")
    op.drop_constraint("fk_source_files_artifact", "source_files", type_="foreignkey")
    op.drop_column("source_files", "artifact_id")
    op.drop_constraint("fk_users_avatar_artifact", "users", type_="foreignkey")
    op.drop_column("users", "avatar_artifact_id")
    op.drop_index("ix_file_artifacts_lifecycle", table_name="file_artifacts")
    op.drop_index("ix_file_artifacts_domain_id", table_name="file_artifacts")
    op.drop_index("ix_file_artifacts_domain_parent_id", table_name="file_artifacts")
    op.drop_index("ix_file_artifacts_owner_user_id", table_name="file_artifacts")
    op.drop_table("file_artifacts")
