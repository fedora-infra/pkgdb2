"""add the monitor field in the Package table

Revision ID: 2947b3065e9a
Revises: 7fa622e911d
Create Date: 2014-10-10 17:16:29.131691

"""

# revision identifiers, used by Alembic.
revision = '2947b3065e9a'
down_revision = '7fa622e911d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ''' Add the `monitor` column on the Package table. '''
    op.add_column(
        'Package',
        sa.Column('monitor', sa.Boolean, default=False)
    )

    ins = "UPDATE \"Package\" SET monitor=FALSE;"
    op.execute(ins)

    op.alter_column('Package',
                    column_name='monitor',
                    nullable=False,
                    existing_nullable=True,
                    )


def downgrade():
    ''' Drop the `monitor` column of the Package table. '''
    op.drop_column('Package', 'monitor')
