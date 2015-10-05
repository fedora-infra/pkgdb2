"""Update unique constraints on admin_actions

Revision ID: 80939061434
Revises: 1f179f37f12b
Create Date: 2015-10-05 11:16:07.256121

"""

# revision identifiers, used by Alembic.
revision = '80939061434'
down_revision = '1f179f37f12b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    """ Drop status from the unique constraing of the admin_actions table.
    """
    op.drop_constraint(
        "admin_actions_user_action_status_package_id_collection_id_key",
        "admin_actions",
        type_='unique',
    )
    op.create_unique_constraint(
        "admin_actions_user_action_package_id_collection_id_key",
        "admin_actions",
        ['user', 'action', 'package_id', 'collection_id'],
    )


def downgrade():
    """ Add status to the unique constraing of the admin_actions table. """
    op.drop_constraint(
        "admin_actions_user_action_package_id_collection_id_key",
        "admin_actions",
        type_='unique',
    )
    op.create_unique_constraint(
        "admin_actions_user_action_status_package_id_collection_id_key",
        "admin_actions",
        ['user', 'action', 'status', 'package_id', 'collection_id'],
    )
