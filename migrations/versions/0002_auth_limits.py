"""Persist authentication rate limits across function instances."""
import sqlalchemy as sa
from alembic import op

revision = "0002_auth_limits"
down_revision = "0001_store"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("auth_rate_limits",
                    sa.Column("key", sa.String(64), primary_key=True),
                    sa.Column("bucket", sa.Integer, primary_key=True),
                    sa.Column("attempts", sa.Integer, nullable=False),
                    if_not_exists=True)
    op.create_index("ix_auth_rate_limits_bucket", "auth_rate_limits", ["bucket"], if_not_exists=True)


def downgrade():
    op.drop_table("auth_rate_limits")
