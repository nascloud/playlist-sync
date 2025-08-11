"""Add verify_ssl to settings

Revision ID: b61164421e06
Revises: 96d5de9f8b95
Create Date: 2025-08-11 15:29:17.935292

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b61164421e06'
down_revision: Union[str, None] = 'a31a7efe82af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('verify_ssl', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade() -> None:
    with op.batch_alter_table('settings', schema=None) as batch_op:
        batch_op.drop_column('verify_ssl')
