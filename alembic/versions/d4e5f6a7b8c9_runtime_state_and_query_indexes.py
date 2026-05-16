"""runtime state and query indexes

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('visits', sa.Column('last_weight_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_visits_cat_id_started_at', 'visits', ['cat_id', 'started_at'], unique=False)
    op.create_index('ix_cleaning_cycles_started_at', 'cleaning_cycles', ['started_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_cleaning_cycles_started_at', table_name='cleaning_cycles')
    op.drop_index('ix_visits_cat_id_started_at', table_name='visits')
    op.drop_column('visits', 'last_weight_at')
