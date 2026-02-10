"""add_node_parameters

Revision ID: 9a1b2c3d4e5f
Revises: 7f8a9b2c3d4e
Create Date: 2026-02-06 21:02:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a1b2c3d4e5f'
down_revision = '7f8a9b2c3d4e'
branch_labels = None
depends_on = None


def upgrade():
    # Add attachment_filenames column to nodes table
    op.add_column('nodes', sa.Column('attachment_filenames', sa.Text(), nullable=True))
    
    # Add prompt_sent column to nodes table
    op.add_column('nodes', sa.Column('prompt_sent', sa.Text(), nullable=True))


def downgrade():
    # Remove columns in reverse order
    op.drop_column('nodes', 'prompt_sent')
    op.drop_column('nodes', 'attachment_filenames')
