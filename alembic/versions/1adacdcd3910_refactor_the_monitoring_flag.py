"""Refactor the monitoring flag

Revision ID: 1adacdcd3910
Revises: 2947b3065e9a
Create Date: 2015-05-18 18:38:11.773711

"""

# revision identifiers, used by Alembic.
revision = '1adacdcd3910'
down_revision = '2947b3065e9a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    """ Update the monitoring column from boolean to text """
    op.alter_column('Package', 'monitor',
                    type_=sa.String(10),
                    existing_type=sa.Boolean(),
                    )


def downgrade():
    """ Update the monitoring column from text to boolean """
    op.alter_column('Package', 'monitor',
                    type_=sa.Boolean(),
                    existing_type=sa.String(10),
                    )
