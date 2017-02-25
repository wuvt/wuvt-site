"""add role models

Revision ID: c4b654dc2af1
Revises: 8c2e1e29d473
Create Date: 2017-02-19 08:30:49.304844

"""

# revision identifiers, used by Alembic.
revision = 'c4b654dc2af1'
down_revision = '8c2e1e29d473'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('group_role',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('group', sa.Unicode(length=255), nullable=False),
    sa.Column('role', sa.Unicode(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_role',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('role', sa.Unicode(length=255), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('user_role')
    op.drop_table('group_role')
