"""mark legacy timeout durations untrusted

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-05-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd8e9f0a1b2c3'
down_revision: Union[str, Sequence[str], None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Hide old timeout fallback durations that predate duration evidence metadata."""
    op.execute(
        """
        UPDATE visits
        SET duration_source = 'hard_timeout',
            duration_is_estimated = true,
            duration_seconds = NULL
        WHERE duration_source = 'unknown'
          AND duration_is_estimated = false
          AND duration_seconds >= 1800
        """
    )


def downgrade() -> None:
    """Data cleanup is intentionally not reversible."""
    pass
