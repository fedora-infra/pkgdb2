"""lower case table name

Revision ID: 2eef3c8402d0
Revises: 187e9f9ec178
Create Date: 2016-09-01 10:22:12.915860

"""

# revision identifiers, used by Alembic.
revision = '2eef3c8402d0'
down_revision = '187e9f9ec178'

from alembic import op
import sqlalchemy as sa

TABLES = {
    'PkgAcls': 'pkg_acls',
    'PkgStatus': 'pkg_status',
    'AclStatus': 'acl_status',
    'CollecStatus': 'collection_status',
    'PackageListingAcl': 'package_listing_acl',
    'Collection': 'collection',
    'PackageListing': 'package_listing',
    'Package': 'package',
    'Log': 'log',
}


def upgrade():
    """ Set all the table names to lower case to make it easier to write
    sql query manually on postgresql. """
    for table in TABLES:
        op.rename_table(table, TABLES[table])


def downgrade():
    """ Set all the table names back to be camel case. """
    # Invert the dict
    old_tables = {TABLES[table]: table for table in TABLES}

    for table in TABLES:
        op.rename_table(table, TABLES[table])
