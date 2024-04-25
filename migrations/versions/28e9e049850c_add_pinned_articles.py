"""add pinned articles

Revision ID: 28e9e049850c
Revises: 5981b26ae993
Create Date: 2024-04-16 21:36:37.723311

"""

# revision identifiers, used by Alembic.
revision = '28e9e049850c'
down_revision = '5981b26ae993'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column("article", sa.Column("pinned_article", sa.Boolean(), nullable=False, server_default="0"))
    op.add_column("article_revision", sa.Column("pinned_article", sa.Boolean(), nullable=False, server_default="0"))
    pass


def downgrade():
    op.drop_column("article", "pinned_article")
    op.drop_column("article_revision", "pinned_article")
    pass
