"""update orders schema

Revision ID: 804fb3dc434f
Revises: 0b247712cf8d
Create Date: 2017-10-22 01:04:51.056818

"""

# revision identifiers, used by Alembic.
revision = '804fb3dc434f'
down_revision = '0b247712cf8d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('orders', sa.Column('donor_comment', sa.UnicodeText(), nullable=True))
    op.add_column('orders', sa.Column('remote_addr', sa.Unicode(length=50), nullable=True))
    op.add_column('orders', sa.Column('user_agent', sa.Unicode(length=255), nullable=True))


def downgrade():
    op.drop_column('orders', 'user_agent')
    op.drop_column('orders', 'remote_addr')
    op.drop_column('orders', 'donor_comment')
