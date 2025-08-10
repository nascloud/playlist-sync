"""Add updated_at back to download_sessions

Revision ID: 8d6a5034447d
Revises: 88eb43329e9b
Create Date: 2025-08-09 20:40:27.312642

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d6a5034447d'
down_revision: Union[str, None] = '88eb43329e9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('download_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('updated_at', sa.DATETIME(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('download_sessions', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
