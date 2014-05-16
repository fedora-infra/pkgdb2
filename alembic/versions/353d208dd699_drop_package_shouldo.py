"""Drop Package.shouldopen

Revision ID: 353d208dd699
Revises: None
Create Date: 2014-05-16 10:08:22.174142

"""

# revision identifiers, used by Alembic.
revision = '353d208dd699'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('Package', 'shouldopen')


def downgrade():
    op.add_column(
        'Package',
        sa.Column('shouldopen', sa.boolean, default=True, nullable=False)
    )
