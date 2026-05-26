"""add secure auth columns to pos terminal

Revision ID: 8aa3587f0f7e
Revises: 001_pos_terminals
Create Date: 2026-05-26 19:51:25.676449

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8aa3587f0f7e'
down_revision: Union[str, Sequence[str], None] = '001_pos_terminals'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('pos_terminals', sa.Column('device_id', sa.String(length=255), nullable=True))
    op.add_column('pos_terminals', sa.Column('last_device_id', sa.String(length=255), nullable=True))
    op.add_column('pos_terminals', sa.Column('operator_pin', sa.String(length=255), nullable=True))
    op.add_column('pos_terminals', sa.Column('authorized_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('idx_terminal_device_id', 'pos_terminals', ['device_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_terminal_device_id', table_name='pos_terminals')
    op.drop_column('pos_terminals', 'authorized_at')
    op.drop_column('pos_terminals', 'operator_pin')
    op.drop_column('pos_terminals', 'last_device_id')
    op.drop_column('pos_terminals', 'device_id')
