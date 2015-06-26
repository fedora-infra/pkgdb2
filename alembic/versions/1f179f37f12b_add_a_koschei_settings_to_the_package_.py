"""Add a koschei settings to the package table

Revision ID: 1f179f37f12b
Revises: 1adacdcd3910
Create Date: 2015-06-26 10:38:16.996889

"""

# revision identifiers, used by Alembic.
revision = '1f179f37f12b'
down_revision = '1adacdcd3910'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ''' Add the `koschei` column on the Package table. '''
    op.add_column(
        'Package',
        sa.Column(
            'koschei',
            sa.Boolean,
            default=False,
            server_default='False',
            nullable=False)
    )


def downgrade():
    ''' Drop the `koschei` column of the Package table. '''
    op.drop_column('Package', 'koschei')
