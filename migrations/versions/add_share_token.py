"""Add share_token field to User model

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2023-08-10 12:34:56.789012

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('share_token', sa.String(64), nullable=True))
    op.create_index(op.f('ix_user_share_token'), 'user', ['share_token'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_user_share_token'), table_name='user')
    op.drop_column('user', 'share_token')