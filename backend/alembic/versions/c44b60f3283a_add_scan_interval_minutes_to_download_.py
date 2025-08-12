"""add_scan_interval_minutes_to_download_settings

Revision ID: c44b60f3283a
Revises: b61164421e06
Create Date: 2025-08-12 11:07:05.365715

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c44b60f3283a'
down_revision: Union[str, None] = 'b61164421e06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('download_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('scan_interval_minutes', sa.Integer(), nullable=True, server_default='30'))


def downgrade() -> None:
    with op.batch_alter_table('download_settings', schema=None) as batch_op:
        batch_op.drop_column('scan_interval_minutes')
