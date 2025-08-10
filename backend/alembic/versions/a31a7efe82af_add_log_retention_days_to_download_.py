"""Add log_retention_days and fix table structures

Revision ID: a31a7efe82af
Revises: b1a2c3d4e5f6
Create Date: 2025-08-09 20:27:27.864650

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a31a7efe82af'
down_revision: Union[str, None] = 'b1a2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 使用批处理模式来兼容 SQLite 的 ALTER TABLE 限制
    with op.batch_alter_table('download_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('log_retention_days', sa.Integer(), nullable=False, server_default='30'))

    with op.batch_alter_table('download_queue', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
        batch_op.drop_column('platform')

    with op.batch_alter_table('download_sessions', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
        batch_op.drop_column('updated_at')

    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
        batch_op.drop_column('status_message')


def downgrade() -> None:
    # 同样使用批处理模式进行回滚
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status_message', sa.VARCHAR(), nullable=True))
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))

    with op.batch_alter_table('download_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('updated_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False))
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))

    with op.batch_alter_table('download_queue', schema=None) as batch_op:
        batch_op.add_column(sa.Column('platform', sa.VARCHAR(), nullable=True))
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))

    with op.batch_alter_table('download_settings', schema=None) as batch_op:
        batch_op.drop_column('log_retention_days')
