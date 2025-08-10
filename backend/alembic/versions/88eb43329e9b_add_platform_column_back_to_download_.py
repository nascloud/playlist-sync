"""Add platform column back to download_queue

Revision ID: 88eb43329e9b
Revises: a31a7efe82af
Create Date: 2025-08-09 20:38:10.614797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '88eb43329e9b'
down_revision: Union[str, None] = 'a31a7efe82af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('download_queue', schema=None) as batch_op:
        batch_op.add_column(sa.Column('platform', sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('download_queue', schema=None) as batch_op:
        batch_op.drop_column('platform')
