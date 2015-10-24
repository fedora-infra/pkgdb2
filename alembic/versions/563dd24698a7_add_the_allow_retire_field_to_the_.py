"""Add the allow_retire field to the collection table

Revision ID: 563dd24698a7
Revises: 80939061434
Create Date: 2015-10-20 17:14:40.996865

"""

# revision identifiers, used by Alembic.
revision = '563dd24698a7'
down_revision = '80939061434'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ''' Add the `allow_retire` column on the Collection table. '''
    op.add_column(
        'Collection',
        sa.Column(
            'allow_retire',
            sa.Boolean,
            default=False,
            server_default='False',
            nullable=True)
    )
    # Set True to EPEL - correct behavior
    op.execute('''UPDATE "Collection" '''
               '''SET allow_retire=TRUE WHERE name='Fedora EPEL';''')
    # Set FALSE to all EOL releases - correct behavior
    op.execute('''UPDATE "Collection" '''
               '''SET allow_retire=FALSE WHERE status='EOL';''')
    # Set True to all releases Under Development - mostly correct, except for
    # after final freeze
    op.execute('''UPDATE "Collection" '''
               '''SET allow_retire=TRUE WHERE status='Under Development';''')

    op.alter_column(
        'Collection',
        column_name='allow_retire',
        nullable=False,
        existing_nullable=True)


def downgrade():
    ''' Drop the `allow_retire` column of the Collection table. '''
    op.drop_column('Collection', 'allow_retire')
