"""add shelly_id in ShellyEM table

Revision ID: b38a56bf6ad3
Revises: e16a3e415063
Create Date: 2026-05-31 21:38:43.205896

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b38a56bf6ad3'
down_revision: Union[str, Sequence[str], None] = 'e16a3e415063'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'energy_meter',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_type', sa.String(length=50), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('brand', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('ip', sa.String(length=50), nullable=True),
        sa.Column('location', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # Drop tables with unnamed FKs to electrical_meter before dropping that
    # table — SQLite cannot rename unnamed FK constraints in batch mode.
    op.drop_table('shelly_em')
    op.drop_table('em_metric')
    op.drop_table('electrical_meter')

    op.create_table(
        'em_metric',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('em_id', sa.Integer(), nullable=False),
        sa.Column('total_act_power', sa.Float(precision=3), nullable=False),
        sa.Column('total_aprt_power', sa.Float(precision=3), nullable=False),
        sa.Column('total_current', sa.Float(precision=3), nullable=False),
        sa.Column('total_act_energy', sa.Float(precision=3), nullable=False),
        sa.Column('total_act_ret_energy', sa.Float(precision=3), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['em_id'], ['energy_meter.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_em_metric_time', 'em_metric', ['em_id', 'recorded_at'], unique=False)

    op.create_table(
        'energy_phase',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('em_metric_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=10), nullable=False),
        sa.Column('current', sa.Float(precision=3), nullable=False),
        sa.Column('voltage', sa.Float(precision=3), nullable=False),
        sa.Column('act_power', sa.Float(precision=3), nullable=False),
        sa.Column('aprt_power', sa.Float(precision=3), nullable=False),
        sa.Column('freq', sa.Float(precision=3), nullable=False),
        sa.Column('pf', sa.Float(precision=3), nullable=False),
        sa.Column('total_act_energy', sa.Float(precision=3), nullable=False),
        sa.Column('total_act_ret_energy', sa.Float(precision=3), nullable=False),
        sa.ForeignKeyConstraint(['em_metric_id'], ['em_metric.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'shelly_em',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shelly_id', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['id'], ['energy_meter.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        'electrical_meter',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('device_type', sa.VARCHAR(length=50), nullable=False),
        sa.Column('enabled', sa.BOOLEAN(), nullable=False),
        sa.Column('brand', sa.VARCHAR(length=50), nullable=False),
        sa.Column('model', sa.VARCHAR(length=50), nullable=False),
        sa.Column('name', sa.VARCHAR(length=50), nullable=False),
        sa.Column('ip', sa.VARCHAR(length=50), nullable=True),
        sa.Column('location', sa.VARCHAR(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.drop_table('shelly_em')
    op.drop_table('energy_phase')
    op.drop_table('em_metric')

    op.create_table(
        'em_metric',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('em_id', sa.Integer(), nullable=False),
        sa.Column('current', sa.Integer(), nullable=False),
        sa.Column('voltage', sa.Float(precision=2), nullable=False),
        sa.Column('power', sa.Float(precision=2), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['em_id'], ['electrical_meter.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_em_metric_time', 'em_metric', ['em_id', 'recorded_at'], unique=False)

    op.create_table(
        'shelly_em',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id'], ['electrical_meter.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.drop_table('energy_meter')
