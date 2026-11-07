"""Track the credential encryption key version without storing key material."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("google_accounts") as batch:
        batch.add_column(
            sa.Column("key_version", sa.String(length=64), nullable=False, server_default="v1")
        )


def downgrade() -> None:
    with op.batch_alter_table("google_accounts") as batch:
        batch.drop_column("key_version")
