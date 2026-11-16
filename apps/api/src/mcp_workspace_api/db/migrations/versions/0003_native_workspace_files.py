"""Track real native Google files without copying their contents into the library."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("messages") as batch:
        batch.add_column(
            sa.Column("workspace_files", sa.JSON(), nullable=False, server_default="[]")
        )
    op.create_table(
        "workspace_files",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.Float(), nullable=False),
        sa.Column(
            "account_id", sa.String(64), sa.ForeignKey("google_accounts.id", ondelete="SET NULL")
        ),
        sa.Column("run_id", sa.String(64), sa.ForeignKey("runs.id", ondelete="SET NULL")),
        sa.Column("artifact_id", sa.String(64), sa.ForeignKey("artifacts.id", ondelete="SET NULL")),
        sa.Column("google_file_id", sa.String(256), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=False),
        sa.Column("web_url", sa.String(), nullable=False),
        sa.Column("revision", sa.String(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.UniqueConstraint("user_id", "google_file_id", name="uq_workspace_file_owner"),
    )
    op.create_index("ix_workspace_files_user_id", "workspace_files", ["user_id"])
    op.create_index("ix_workspace_files_run_id", "workspace_files", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_workspace_files_run_id", table_name="workspace_files")
    op.drop_index("ix_workspace_files_user_id", table_name="workspace_files")
    op.drop_table("workspace_files")
    with op.batch_alter_table("messages") as batch:
        batch.drop_column("workspace_files")
