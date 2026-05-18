"""cat event occurred_at date

Revision ID: c7d8e9f0a1b2
Revises: b6c7d8e9f0a1
Create Date: 2026-05-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, Sequence[str], None] = 'b6c7d8e9f0a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Store cat lifecycle event occurrence as a calendar date."""
    op.alter_column(
        'cat_events',
        'occurred_at',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.Date(),
        existing_nullable=False,
        postgresql_using="(occurred_at AT TIME ZONE 'Europe/Amsterdam')::date",
    )


def downgrade() -> None:
    """Restore cat lifecycle event occurrence as a timezone-aware timestamp."""
    op.alter_column(
        'cat_events',
        'occurred_at',
        existing_type=sa.Date(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        postgresql_using="occurred_at::timestamp AT TIME ZONE 'Europe/Amsterdam'",
    )
