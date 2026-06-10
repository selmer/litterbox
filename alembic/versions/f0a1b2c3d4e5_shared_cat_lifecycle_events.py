"""shared cat lifecycle events

Revision ID: f0a1b2c3d4e5
Revises: e9f0a1b2c3d4
Create Date: 2026-06-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f0a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "e9f0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "cat_event_cats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("cat_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["cat_id"], ["cats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["cat_events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "cat_id", name="uq_cat_event_cats_event_id_cat_id"),
    )
    op.create_index(op.f("ix_cat_event_cats_event_id"), "cat_event_cats", ["event_id"], unique=False)
    op.create_index(op.f("ix_cat_event_cats_cat_id"), "cat_event_cats", ["cat_id"], unique=False)
    op.create_index("ix_cat_event_cats_cat_id_event_id", "cat_event_cats", ["cat_id", "event_id"], unique=False)

    op.execute(
        """
        INSERT INTO cat_event_cats (event_id, cat_id)
        SELECT id, cat_id
        FROM cat_events
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_cat_event_cats_cat_id_event_id", table_name="cat_event_cats")
    op.drop_index(op.f("ix_cat_event_cats_cat_id"), table_name="cat_event_cats")
    op.drop_index(op.f("ix_cat_event_cats_event_id"), table_name="cat_event_cats")
    op.drop_table("cat_event_cats")
