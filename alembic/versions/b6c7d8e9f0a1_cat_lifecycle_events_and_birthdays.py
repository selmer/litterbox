"""cat lifecycle events and birthdays

Revision ID: b6c7d8e9f0a1
Revises: e5f6a7b8c9d0
Create Date: 2026-05-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6c7d8e9f0a1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('cats', sa.Column('birth_date', sa.Date(), nullable=True))
    op.create_table(
        'cat_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cat_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('cost_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('cost_currency', sa.String(length=3), nullable=False, server_default='EUR'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['cat_id'], ['cats.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_cat_events_cat_id'), 'cat_events', ['cat_id'], unique=False)
    op.create_index(op.f('ix_cat_events_occurred_at'), 'cat_events', ['occurred_at'], unique=False)
    op.create_index('ix_cat_events_cat_id_occurred_at', 'cat_events', ['cat_id', 'occurred_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_cat_events_cat_id_occurred_at', table_name='cat_events')
    op.drop_index(op.f('ix_cat_events_occurred_at'), table_name='cat_events')
    op.drop_index(op.f('ix_cat_events_cat_id'), table_name='cat_events')
    op.drop_table('cat_events')
    op.drop_column('cats', 'birth_date')
