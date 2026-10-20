"""Retry persistent object cleanup work recorded by prior API operations."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from paperweave.infrastructure.db.models import FileArtifactRecord


def reconcile_pending_deletes(session: Session, storage) -> tuple[int, int]:
    completed = failed = 0
    rows = list(session.scalars(
        select(FileArtifactRecord)
        .where(
            FileArtifactRecord.lifecycle.in_(("pending_delete", "pending_upload")),
            FileArtifactRecord.created_at < datetime.now(timezone.utc) - timedelta(minutes=15),
        )
        .order_by(FileArtifactRecord.created_at)
        .with_for_update(skip_locked=True)
    ))
    for artifact in rows:
        try:
            storage.delete(artifact.object_key, backend=artifact.backend)
            artifact.lifecycle = "deleted"
            artifact.deleted_at = datetime.now(timezone.utc)
            artifact.last_cleanup_error = None
            completed += 1
        except Exception as exc:
            artifact.cleanup_attempts += 1
            artifact.last_cleanup_error = type(exc).__name__
            failed += 1
    session.commit()
    return completed, failed
