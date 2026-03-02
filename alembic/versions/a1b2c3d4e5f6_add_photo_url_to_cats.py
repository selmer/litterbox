"""add photo_url to cats

Revision ID: a1b2c3d4e5f6
Revises: ec1804d6ab04
Create Date: 2026-03-01 22:43:00.000000

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
    """Add photo_url column to cats table."""
    op.add_column('cats', sa.Column('photo_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove photo_url column from cats table."""
    op.drop_column('cats', 'photo_url')
