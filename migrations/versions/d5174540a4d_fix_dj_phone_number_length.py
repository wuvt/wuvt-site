"""fix DJ phone number length

Revision ID: d5174540a4d
Revises: 187cf9175cee
Create Date: 2015-11-28 19:28:53.680269

"""

# revision identifiers, used by Alembic.
revision = 'd5174540a4d'
down_revision = '187cf9175cee'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('dj', 'phone', type_=sa.Unicode(12))

def downgrade():
    op.alter_column('dj', 'phone', type_=sa.Unicode(10))
