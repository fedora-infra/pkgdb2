"""Expand fas_name to 255 chars

Revision ID: 187e9f9ec178
Revises: 27924040e3ad
Create Date: 2016-07-07 19:54:21.331838

"""

# revision identifiers, used by Alembic.
revision = '187e9f9ec178'
down_revision = '27924040e3ad'

from alembic import op
import sqlalchemy as sa


def upgrade():
    """ Update the fas_name column of PackageListingAcl from 32 chars to 255
    """
    op.alter_column(
        table_name='PackageListingAcl',
        column_name='fas_name',
        type_=sa.String(255),
        existing_type=sa.String(32)
    )


def downgrade():
    """ Update the fas_name column of PackageListingAcl from 255 chars to 32
    """
    op.alter_column(
        table_name='PackageListingAcl',
        column_name='fas_name',
        type_=sa.String(32),
        existing_type=sa.String(255)
    )
