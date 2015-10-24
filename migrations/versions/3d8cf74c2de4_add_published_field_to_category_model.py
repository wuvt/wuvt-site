"""add published field to category model

Revision ID: 3d8cf74c2de4
Revises: None
Create Date: 2015-09-21 22:27:36.166147

"""

# revision identifiers, used by Alembic.
revision = '3d8cf74c2de4'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('category', sa.Column('published', sa.Boolean(),
                                        nullable=False))


def downgrade():
    op.drop_column('category', 'published')
