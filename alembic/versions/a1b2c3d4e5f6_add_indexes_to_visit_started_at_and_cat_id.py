"""add indexes to visit started_at and cat_id

Revision ID: a1b2c3d4e5f6
Revises: ec1804d6ab04
Create Date: 2026-03-07 22:48:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'ec1804d6ab04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index('ix_visits_started_at', 'visits', ['started_at'], unique=False)
    op.create_index('ix_visits_cat_id', 'visits', ['cat_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_visits_cat_id', table_name='visits')
    op.drop_index('ix_visits_started_at', table_name='visits')
