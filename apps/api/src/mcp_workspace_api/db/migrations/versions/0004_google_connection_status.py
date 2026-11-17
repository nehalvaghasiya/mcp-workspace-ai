"""Persist sanitized Google connection health without credential material."""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("google_accounts") as batch:
        batch.add_column(
            sa.Column("connection_error", sa.String(64), nullable=False, server_default="")
        )
        batch.add_column(sa.Column("connection_checked_at", sa.Float(), nullable=True))
        batch.add_column(
            sa.Column("connector_errors", sa.JSON(), nullable=False, server_default="{}")
        )


def downgrade() -> None:
    with op.batch_alter_table("google_accounts") as batch:
        batch.drop_column("connector_errors")
        batch.drop_column("connection_checked_at")
        batch.drop_column("connection_error")
