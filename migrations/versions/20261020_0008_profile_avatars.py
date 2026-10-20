"""Store local profile avatar metadata."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261020_0008"
down_revision: Union[str, None] = "20261019_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_key", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("avatar_media_type", sa.String(length=40), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_media_type")
    op.drop_column("users", "avatar_key")
