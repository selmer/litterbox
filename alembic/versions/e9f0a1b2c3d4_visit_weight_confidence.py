"""visit weight confidence

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-05-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9f0a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'd8e9f0a1b2c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('visits', sa.Column('weight_confidence', sa.String(), nullable=False, server_default='normal'))
    op.add_column('visits', sa.Column('weight_confidence_reason', sa.String(), nullable=True))
    op.create_index('ix_visits_weight_confidence', 'visits', ['weight_confidence'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_visits_weight_confidence', table_name='visits')
    op.drop_column('visits', 'weight_confidence_reason')
    op.drop_column('visits', 'weight_confidence')
