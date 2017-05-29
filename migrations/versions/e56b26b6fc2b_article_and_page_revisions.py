"""Article and page revisions

Revision ID: e56b26b6fc2b
Revises: ac0939a5ff73
Create Date: 2017-04-16 22:25:56.690109

"""

# revision identifiers, used by Alembic.
revision = 'e56b26b6fc2b'
down_revision = 'ac0939a5ff73'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('page_revision',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('page_id', sa.Integer(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.Column('datetime', sa.DateTime(), nullable=True),
    sa.Column('name', sa.Unicode(length=255), nullable=False),
    sa.Column('content', sa.UnicodeText().with_variant(sa.UnicodeText(length=2**1), 'mysql'), nullable=False),
    sa.Column('html', sa.UnicodeText().with_variant(sa.UnicodeText(length=2**1), 'mysql'), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['page_id'], ['page.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('article_revision',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('article_id', sa.Integer(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.Column('datetime', sa.DateTime(), nullable=True),
    sa.Column('title', sa.Unicode(length=255), nullable=False),
    sa.Column('summary', sa.UnicodeText().with_variant(sa.UnicodeText(length=2**1), 'mysql'), nullable=True),
    sa.Column('content', sa.UnicodeText().with_variant(sa.UnicodeText(length=2**1), 'mysql'), nullable=True),
    sa.Column('html_summary', sa.UnicodeText().with_variant(sa.UnicodeText(length=2**1), 'mysql'), nullable=True),
    sa.Column('html_content', sa.UnicodeText().with_variant(sa.UnicodeText(length=2**1), 'mysql'), nullable=True),
    sa.ForeignKeyConstraint(['article_id'], ['article.id'], ),
    sa.ForeignKeyConstraint(['author_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('article_revision')
    op.drop_table('page_revision')
