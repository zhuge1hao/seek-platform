"""v1.8 initial APP PostgreSQL schema"""

from alembic import op

from db.base import metadata
from db.models import define_tables, TABLE_NAMES


revision = "20260705_v18_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not all(table_name in metadata.tables for table_name in TABLE_NAMES):
        define_tables(metadata)
    for table_name in TABLE_NAMES:
        metadata.tables[table_name].create(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    raise RuntimeError("Production downgrade is intentionally disabled; restore from backup instead.")
