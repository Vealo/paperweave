"""Normalize persisted user theme preferences to light."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261020_0011"
down_revision: Union[str, None] = "20261020_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Theme is the only user setting in this migration; keep every other row
    # and user attribute untouched while retiring unsupported values.
    op.execute(sa.text("UPDATE user_settings SET theme = 'light' WHERE theme <> 'light'"))
    op.alter_column("user_settings", "theme", server_default="light")
    op.create_check_constraint(
        "ck_user_settings_theme_light", "user_settings", "theme = 'light'"
    )


def downgrade() -> None:
    op.drop_constraint("ck_user_settings_theme_light", "user_settings", type_="check")
    op.alter_column("user_settings", "theme", server_default="system")
