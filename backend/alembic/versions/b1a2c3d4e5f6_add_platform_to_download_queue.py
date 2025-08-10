"""Add platform column to download_queue table

Revision ID: b1a2c3d4e5f6
Revises: a9fe5e8861c8
Create Date: 2025-08-09 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1a2c3d4e5f6'
down_revision: Union[str, None] = 'a9fe5e8861c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('download_queue', schema=None) as batch_op:
        batch_op.add_column(sa.Column('platform', sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('download_queue', schema=None) as batch_op:
        batch_op.drop_column('platform')
