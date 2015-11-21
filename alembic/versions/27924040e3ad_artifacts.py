"""artifacts


Revision ID: 27924040e3ad
Revises: 33d905fb1f55
Create Date: 2015-11-21 11:59:21.906604

"""

# revision identifiers, used by Alembic.
revision = '27924040e3ad'
down_revision = '33d905fb1f55'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ''' Add the artifact field to the Package table, fill it and adjust
    the unique key constraints.
    '''

    op.add_column(
        'Package',
        sa.Column(
            'artifact',
            sa.String(50),
            sa.ForeignKey('artifacts.artifact', onupdate='CASCADE'),
            default='rpms',
        )
    )

    op.execute('''UPDATE "Package" SET artifact='rpms';''')

    op.alter_column(
        'Package',
        column_name='artifact',
        nullable=False,
        existing_nullable=True)

    op.execute("""
DROP INDEX "ix_Package_name";
ALTER TABLE "Package"
  ADD CONSTRAINT "ix_package_name_artifact" UNIQUE (name, artifact);
""")


def downgrade():
    ''' Drop the artifact field to the Package table and adjust the unique
    key constraints.
    '''
    op.drop_column('Package', 'artifact')
