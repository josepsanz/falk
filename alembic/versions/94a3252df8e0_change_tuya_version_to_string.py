"""change tuya_switch.version from Float to String

Revision ID: 94a3252df8e0
Revises: b38a56bf6ad3
Create Date: 2026-05-31 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '94a3252df8e0'
down_revision: Union[str, Sequence[str], None] = 'b38a56bf6ad3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('tuya_switch', schema=None) as batch_op:
        batch_op.alter_column(
            'version',
            existing_type=sa.Float(),
            type_=sa.String(length=16),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('tuya_switch', schema=None) as batch_op:
        batch_op.alter_column(
            'version',
            existing_type=sa.String(length=16),
            type_=sa.Float(),
            existing_nullable=False,
        )
