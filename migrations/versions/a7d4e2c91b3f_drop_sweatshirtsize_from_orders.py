"""drop sweatshirtsize from orders

Revision ID: a7d4e2c91b3f
Revises: f3a1c9d2b7e4
Create Date: 2026-10-19 09:45:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'a7d4e2c91b3f'
down_revision = 'f3a1c9d2b7e4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('orders', 'sweatshirtsize')


def downgrade():
    # restores the column only; the dropped data cannot be recovered
    op.add_column('orders', sa.Column('sweatshirtsize', sa.Unicode(length=255), nullable=True))
