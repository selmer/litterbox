"""visit duration evidence and diagnostics

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('visits', sa.Column('duration_source', sa.String(), nullable=False, server_default='unknown'))
    op.add_column('visits', sa.Column('duration_is_estimated', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table(
        'visit_diagnostics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('visit_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['visit_id'], ['visits.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_visit_diagnostics_visit_id'), 'visit_diagnostics', ['visit_id'], unique=False)
    op.create_index('ix_visit_diagnostics_visit_id_recorded_at', 'visit_diagnostics', ['visit_id', 'recorded_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_visit_diagnostics_visit_id_recorded_at', table_name='visit_diagnostics')
    op.drop_index(op.f('ix_visit_diagnostics_visit_id'), table_name='visit_diagnostics')
    op.drop_table('visit_diagnostics')
    op.drop_column('visits', 'duration_is_estimated')
    op.drop_column('visits', 'duration_source')
