"""Add MBID columns

Revision ID: 8c2e1e29d473
Revises: 52899175817
Create Date: 2016-10-17 04:32:15.202037

"""

# revision identifiers, used by Alembic.
revision = '8c2e1e29d473'
down_revision = '52899175817'

from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils import UUIDType


def upgrade():
    op.add_column('track', sa.Column('artist_mbid', UUIDType(), nullable=True))
    op.add_column('track', sa.Column('recording_mbid', UUIDType(), nullable=True))
    op.add_column('track', sa.Column('release_mbid', UUIDType(), nullable=True))
    op.add_column('track', sa.Column('releasegroup_mbid', UUIDType(), nullable=True))


def downgrade():
    op.drop_column('track', 'releasegroup_mbid')
    op.drop_column('track', 'release_mbid')
    op.drop_column('track', 'recording_mbid')
    op.drop_column('track', 'artist_mbid')
