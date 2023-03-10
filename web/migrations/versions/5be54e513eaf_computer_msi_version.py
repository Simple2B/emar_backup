"""computer msi_version

Revision ID: 5be54e513eaf
Revises: 9a29b86291dd
Create Date: 2023-02-16 21:17:56.941153

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5be54e513eaf'
down_revision = '9a29b86291dd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('computers', sa.Column('msi_version', sa.String(length=64), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('computers', 'msi_version')
    # ### end Alembic commands ###
