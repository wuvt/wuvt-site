"""add listen_method to orders

Revision ID: f3a1c9d2b7e4
Revises: 28e9e049850c
Create Date: 2026-10-19 09:45:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'f3a1c9d2b7e4'
down_revision = '28e9e049850c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('orders', sa.Column('listen_method', sa.Unicode(length=255), nullable=True))


def downgrade():
    op.drop_column('orders', 'listen_method')
