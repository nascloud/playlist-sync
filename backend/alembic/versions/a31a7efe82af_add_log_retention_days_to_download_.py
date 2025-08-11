"""Add log_retention_days and fix table structures

Revision ID: a31a7efe82af
Revises: c01cd43e0783
Create Date: 2025-08-09 20:27:27.864650

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a31a7efe82af'
down_revision: Union[str, None] = 'c01cd43e0783' # 指向初始迁移
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('download_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('log_retention_days', sa.Integer(), nullable=True, server_default='30'))

    with op.batch_alter_table('download_queue', schema=None) as batch_op:
        batch_op.add_column(sa.Column('platform', sa.String(), nullable=True))

    with op.batch_alter_table('download_sessions', schema=None) as batch_op:
        pass # updated_at 已经由初始迁移创建，无需操作

    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status_message', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_column('status_message')

    with op.batch_alter_table('download_sessions', schema=None) as batch_op:
        batch_op.drop_column('updated_at')

    with op.batch_alter_table('download_queue', schema=None) as batch_op:
        batch_op.drop_column('platform')

    with op.batch_alter_table('download_settings', schema=None) as batch_op:
        batch_op.drop_column('log_retention_days')
