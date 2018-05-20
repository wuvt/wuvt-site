"""Drop Trackman tables

Revision ID: 5981b26ae993
Revises: 804fb3dc434f
Create Date: 2018-05-19 23:57:42.897891

"""

# revision identifiers, used by Alembic.
revision = '5981b26ae993'
down_revision = '804fb3dc434f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_table('air_log')
    op.drop_table('tracklog')
    op.drop_table('trackreport')
    op.drop_table('track')
    op.drop_table('set')
    op.drop_table('dj')
    op.drop_table('rotation')


def downgrade():
    raise Exception("Downgrade to previous versions is unsupported.")
