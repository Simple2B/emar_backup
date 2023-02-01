"""last downloaded folder

Revision ID: fd03461f5c2e
Revises: 632045337307
Create Date: 2023-01-27 16:58:16.155823

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd03461f5c2e'
down_revision = '632045337307'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('computers', sa.Column('last_downloaded', sa.String(length=256), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('computers', 'last_downloaded')
    # ### end Alembic commands ###