"""user for web only, added computer, location, company

Revision ID: 7795f8209b66
Revises: 255015bb45d7
Create Date: 2023-01-18 16:55:50.389830

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7795f8209b66'
down_revision = '255015bb45d7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('companies',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('locations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('company_name', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['company_name'], ['companies.name'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('computers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('computer_name', sa.String(length=64), nullable=False),
    sa.Column('location_name', sa.String(), nullable=False),
    sa.Column('type', sa.String(length=128), nullable=True),
    sa.Column('alert_status', sa.String(length=128), nullable=True),
    sa.Column('activated', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('sftp_host', sa.String(length=128), nullable=True),
    sa.Column('sftp_username', sa.String(length=64), nullable=True),
    sa.Column('sftp_password', sa.String(length=128), nullable=True),
    sa.Column('sftp_folder_path', sa.String(length=256), nullable=True),
    sa.Column('folder_password', sa.String(length=128), nullable=True),
    sa.Column('download_status', sa.String(length=64), nullable=True),
    sa.Column('last_download_time', sa.DateTime(), nullable=True),
    sa.Column('last_time_online', sa.DateTime(), nullable=True),
    sa.Column('identifier_key', sa.String(length=128), nullable=True),
    sa.Column('company_name', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['company_name'], ['companies.name'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['location_name'], ['locations.name'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('computer_name')
    )
    op.drop_column('users', 'sftp_folder_path')
    op.drop_column('users', 'last_download_time')
    op.drop_column('users', 'identifier_key')
    op.drop_column('users', 'location')
    op.drop_column('users', 'sftp_host')
    op.drop_column('users', 'sftp_username')
    op.drop_column('users', 'folder_password')
    op.drop_column('users', 'client')
    op.drop_column('users', 'sftp_password')
    op.drop_column('users', 'download_status')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('download_status', sa.VARCHAR(length=64), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('sftp_password', sa.VARCHAR(length=128), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('client', sa.VARCHAR(length=128), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('folder_password', sa.VARCHAR(length=128), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('sftp_username', sa.VARCHAR(length=64), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('sftp_host', sa.VARCHAR(length=128), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('location', sa.VARCHAR(length=128), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('identifier_key', sa.VARCHAR(length=128), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('last_download_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('sftp_folder_path', sa.VARCHAR(length=256), autoincrement=False, nullable=True))
    op.drop_table('computers')
    op.drop_table('locations')
    op.drop_table('companies')
    # ### end Alembic commands ###