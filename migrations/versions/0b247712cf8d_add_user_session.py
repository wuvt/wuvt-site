"""add user_session

Revision ID: 0b247712cf8d
Revises: e56b26b6fc2b
Create Date: 2017-05-30 05:40:34.700792

"""

# revision identifiers, used by Alembic.
revision = '0b247712cf8d'
down_revision = 'e56b26b6fc2b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('user_session',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('login_at', sa.DateTime(), nullable=True),
    sa.Column('expires', sa.DateTime(), nullable=True),
    sa.Column('user_agent', sa.Unicode(length=512), nullable=True),
    sa.Column('remote_addr', sa.Unicode(length=100), nullable=True),
    sa.Column('roles_list', sa.Unicode(length=1024), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('user_session')
