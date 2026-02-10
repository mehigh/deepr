"""add attachments table

Revision ID: 7f8a9b2c3d4e
Revises: 424ef138cd54
Create Date: 2026-02-05 23:14:21.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f8a9b2c3d4e'
down_revision = '424ef138cd54'
branch_labels = None
depends_on = None


def upgrade():
    # Create attachments table
    op.create_table(
        'attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_data', sa.LargeBinary(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_attachments_node_id', 'attachments', ['node_id'])
    op.create_index('idx_attachments_created_at', 'attachments', ['created_at'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_attachments_created_at', table_name='attachments')
    op.drop_index('idx_attachments_node_id', table_name='attachments')
    
    # Drop table
    op.drop_table('attachments')
