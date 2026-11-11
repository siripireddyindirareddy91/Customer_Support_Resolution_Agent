"""Create the initial application stores."""
import sqlalchemy as sa
from alembic import op

revision = "0001_store"
down_revision = None
branch_labels = None
depends_on = None
TABLES = ("users", "investigations", "policy_documents", "audit_events", "evaluation_runs", "orders", "tracking_events")


def upgrade():
    for name in TABLES:
        op.create_table(name,
                        sa.Column("id", sa.String(128), primary_key=True),
                        sa.Column("owner", sa.String(128), nullable=False),
                        sa.Column("payload", sa.JSON(), nullable=False),
                        if_not_exists=True)
        op.create_index(f"ix_{name}_owner", name, ["owner"], if_not_exists=True)


def downgrade():
    for name in reversed(TABLES):
        op.drop_table(name)
