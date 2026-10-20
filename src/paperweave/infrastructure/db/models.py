"""Persistence records mapped to the relational schema."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid, func, UniqueConstraint, BigInteger, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paperweave.infrastructure.db.base import Base


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    avatar_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_media_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    avatar_artifact_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("file_artifacts.id", ondelete="SET NULL", use_alter=True, name="fk_users_avatar_artifact"), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class UserSettingsRecord(Base):
    __tablename__ = "user_settings"
    __table_args__ = (
        CheckConstraint("theme = 'light'", name="ck_user_settings_theme_light"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    theme: Mapped[str] = mapped_column(String(10), nullable=False, default="light", server_default="light")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SessionRecord(Base):
    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class ProjectRecord(Base):
    __tablename__ = "projects"

    owner_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ManuscriptRecord(Base):
    __tablename__ = "manuscripts"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class ManuscriptRevisionRecord(Base):
    __tablename__ = "manuscript_revisions"
    __table_args__ = (UniqueConstraint("manuscript_id", "version", name="uq_manuscript_revisions_manuscript_version"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    manuscript_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("manuscripts.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AIProposalRecord(Base):
    __tablename__ = "ai_proposals"
    __table_args__ = (UniqueConstraint("project_id", "idempotency_key", name="uq_ai_proposals_project_idempotency"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    manuscript_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("manuscripts.id", ondelete="CASCADE"), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    target_version: Mapped[int] = mapped_column(Integer, nullable=False)
    target_position: Mapped[int] = mapped_column(Integer, nullable=False)
    context_manifest: Mapped[dict] = mapped_column(JSONB, nullable=False)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    reviewer_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class SourceRecord(Base):
    __tablename__ = "sources"
    __table_args__ = (UniqueConstraint("project_id", "doi", name="uq_sources_project_doi"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    authors: Mapped[str | None] = mapped_column(Text, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_provenance: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SourceFileRecord(Base):
    __tablename__ = "source_files"
    __table_args__ = (UniqueConstraint("source_id", "version", name="uq_source_files_source_version"), UniqueConstraint("source_id", "sha256", name="uq_source_files_source_sha256"))

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    media_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    artifact_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("file_artifacts.id", ondelete="RESTRICT"), nullable=True, unique=True)
    artifact: Mapped["FileArtifactRecord | None"] = relationship("FileArtifactRecord", foreign_keys=[artifact_id])
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class FileArtifactRecord(Base):
    __tablename__ = "file_artifacts"
    __table_args__ = (
        UniqueConstraint("backend", "bucket", "object_key", name="uq_file_artifacts_backend_object"),
        UniqueConstraint("owner_user_id", "idempotency_key", name="uq_file_artifacts_owner_idempotency"),
        CheckConstraint("kind IN ('avatar', 'image', 'document')", name="ck_file_artifacts_kind"),
        CheckConstraint("lifecycle IN ('pending_upload', 'active', 'pending_delete', 'deleted', 'failed')", name="ck_file_artifacts_lifecycle"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    domain_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    domain_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    domain_parent_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    backend: Mapped[str] = mapped_column(String(16), nullable=False)
    bucket: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    media_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    lifecycle: Mapped[str] = mapped_column(String(24), nullable=False, default="pending_upload", index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    cleanup_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_cleanup_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SourceFileReferenceRecord(Base):
    """Generic durable links owned by later domains (passages, evidence)."""
    __tablename__ = "source_file_references"
    __table_args__ = (UniqueConstraint("file_id", "reference_type", "reference_id", name="uq_source_file_reference"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    file_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("source_files.id", ondelete="RESTRICT"), nullable=False, index=True)
    reference_type: Mapped[str] = mapped_column(String(40), nullable=False)
    reference_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    review_state: Mapped[str] = mapped_column(String(24), nullable=False, default="active", server_default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ExtractionRunRecord(Base):
    __tablename__ = "extraction_runs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    file_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("source_files.id", ondelete="RESTRICT"), nullable=False, index=True)
    processor: Mapped[str] = mapped_column(String(80), nullable=False)
    processor_version: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SourcePassageRecord(Base):
    __tablename__ = "source_passages"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("extraction_runs.id", ondelete="RESTRICT"), nullable=False, index=True)
    file_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("source_files.id", ondelete="RESTRICT"), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ClaimRecord(Base):
    __tablename__ = "claims"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    manuscript_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("manuscripts.id", ondelete="CASCADE"), nullable=False, index=True)
    block_position: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    manuscript_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class EvidenceLinkRecord(Base):
    __tablename__ = "evidence_links"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    claim_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_version: Mapped[int] = mapped_column(Integer, nullable=False)
    passage_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("source_passages.id", ondelete="RESTRICT"), nullable=False, index=True)
    passage_file_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("source_files.id", ondelete="RESTRICT"), nullable=False)
    relation: Mapped[str] = mapped_column(String(24), nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    review_state: Mapped[str] = mapped_column(String(24), nullable=False, default="unreviewed")
    manuscript_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class ReviewDecisionRecord(Base):
    __tablename__ = "review_decisions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    evidence_link_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("evidence_links.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    link_version: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[str] = mapped_column(String(24), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
