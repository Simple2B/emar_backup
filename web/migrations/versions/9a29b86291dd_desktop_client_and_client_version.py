"""desktop client and client version

Revision ID: 9a29b86291dd
Revises: 8de64c2e7f6f
Create Date: 2023-02-16 14:32:11.256871

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a29b86291dd'
down_revision = '8de64c2e7f6f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('client_versions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('desktop_clients',
    sa.Column('mimetype', sa.Unicode(length=255), nullable=False),
    sa.Column('filename', sa.Unicode(length=255), nullable=False),
    sa.Column('blob', sa.LargeBinary(), nullable=False),
    sa.Column('size', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('version', sa.String(length=64), nullable=True),
    sa.Column('description', sa.String(length=512), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('flag_name', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['flag_name'], ['client_versions.name'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('desktop_clients')
    op.drop_table('client_versions')
    # ### end Alembic commands ###