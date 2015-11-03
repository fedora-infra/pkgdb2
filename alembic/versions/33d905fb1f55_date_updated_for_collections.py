"""date_updated for collections

Revision ID: 33d905fb1f55
Revises: 563dd24698a7
Create Date: 2015-11-03 09:47:01.276762

"""

# revision identifiers, used by Alembic.
revision = '33d905fb1f55'
down_revision = '563dd24698a7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ''' Add the column closed_at to the table pull_requests.
    '''
    op.add_column(
        'Collection',
        sa.Column(
            'date_updated',
            sa.DateTime,
            nullable=True,
            default=sa.func.now(),
            onupdate=sa.func.now()
        )
    )

    op.execute('''UPDATE "Collection" SET date_updated=date_created;''')

    op.alter_column(
        'Collection',
        column_name='date_updated',
        nullable=False,
        existing_nullable=True)


def downgrade():
    ''' Drop status from the column date_updated of the Collection table
    '''
    op.drop_column('Collection', 'date_updated')
