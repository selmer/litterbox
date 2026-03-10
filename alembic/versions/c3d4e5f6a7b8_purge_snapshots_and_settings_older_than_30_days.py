"""purge snapshots and settings older than 30 days

Revision ID: c3d4e5f6a7b8
Revises: f1e2d3c4b5a6
Create Date: 2026-03-10 18:21:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'f1e2d3c4b5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RETENTION_DAYS = 30


def upgrade() -> None:
    """Delete rows older than 30 days and add indexes to support future cleanups."""
    # Add indexes first so the deletes (and any future scheduled cleanups) are fast.
    op.create_index('ix_device_snapshots_recorded_at', 'device_snapshots', ['recorded_at'])
    op.create_index('ix_settings_history_changed_at', 'settings_history', ['changed_at'])

    conn = op.get_bind()

    if conn.dialect.name == 'postgresql':
        conn.execute(text(
            f"DELETE FROM device_snapshots WHERE recorded_at < NOW() - INTERVAL '{RETENTION_DAYS} days'"
        ))
        conn.execute(text(
            f"DELETE FROM settings_history WHERE changed_at < NOW() - INTERVAL '{RETENTION_DAYS} days'"
        ))
    else:
        # SQLite
        conn.execute(text(
            f"DELETE FROM device_snapshots "
            f"WHERE recorded_at < datetime('now', '-{RETENTION_DAYS} days')"
        ))
        conn.execute(text(
            f"DELETE FROM settings_history "
            f"WHERE changed_at < datetime('now', '-{RETENTION_DAYS} days')"
        ))


def downgrade() -> None:
    """Remove the indexes added in upgrade. Deleted rows cannot be restored."""
    op.drop_index('ix_settings_history_changed_at', table_name='settings_history')
    op.drop_index('ix_device_snapshots_recorded_at', table_name='device_snapshots')
