"""Increase track column lengths

On Postgres, the columns will be set to unlimited length.

Revision ID: ac0939a5ff73
Revises: c4b654dc2af1
Create Date: 2017-02-25 07:00:15.121508

"""

# revision identifiers, used by Alembic.
revision = 'ac0939a5ff73'
down_revision = 'c4b654dc2af1'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column(
        'track', 'title',
        type_=sa.Unicode(500).with_variant(sa.Unicode, 'postgresql'))
    op.alter_column(
        'track', 'artist',
        type_=sa.Unicode(255).with_variant(sa.Unicode, 'postgresql'))
    op.alter_column(
        'track', 'album',
        type_=sa.Unicode(255).with_variant(sa.Unicode, 'postgresql'))
    op.alter_column(
        'track', 'label',
        type_=sa.Unicode(255).with_variant(sa.Unicode, 'postgresql'))


def downgrade():
    op.alter_column('track', 'title', type_=sa.Unicode(255))
    op.alter_column('track', 'artist', type_=sa.Unicode(255))
    op.alter_column('track', 'album', type_=sa.Unicode(255))
    op.alter_column('track', 'label', type_=sa.Unicode(255))
