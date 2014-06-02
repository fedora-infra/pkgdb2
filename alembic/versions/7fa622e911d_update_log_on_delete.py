"""Update Log on delete

Revision ID: 7fa622e911d
Revises: 353d208dd699
Create Date: 2014-06-02 12:37:09.917179

"""

# revision identifiers, used by Alembic.
revision = '7fa622e911d'
down_revision = '353d208dd699'

from alembic import op
import sqlalchemy as sa


def upgrade():
    """ Set the foreign key package_id of Log to SET NULL on delete. """
    op.execute("""
ALTER TABLE "Log"
DROP CONSTRAINT "Log_package_id_fkey",
ADD CONSTRAINT "Log_package_id_fkey"
   FOREIGN KEY (package_id)
   REFERENCES "Package"(id)
   ON DELETE SET NULL
   ON UPDATE CASCADE;
   """)


def downgrade():
    """ Set back the foreign key package_id of Log to RESTRICT on delete.
    """
    op.execute("""
ALTER TABLE "Log"
DROP CONSTRAINT "Log_package_id_fkey",
ADD CONSTRAINT "Log_package_id_fkey"
   FOREIGN KEY (package_id)
   REFERENCES "Package"(id)
   ON DELETE RESTRICT
   ON UPDATE CASCADE;
   """)
