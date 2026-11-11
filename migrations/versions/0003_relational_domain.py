"""Add foreign-key-backed domain records and snapshot backfill."""
from alembic import op
from backend.main import data_revisions, domain, schema

revision = "0003_relational_domain"
down_revision = "0002_auth_limits"
branch_labels = None
depends_on = None


def upgrade():
    schema.create_all(op.get_bind(), tables=[data_revisions, *domain.tables.values()])


def downgrade():
    schema.drop_all(op.get_bind(), tables=[data_revisions, *domain.tables.values()])
