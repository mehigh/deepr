"""add cost and warnings fields to nodes

Revision ID: b2c3d4e5f6a7
Revises: 9a1b2c3d4e5f
Create Date: 2026-02-06 22:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = '9a1b2c3d4e5f'
branch_labels = None
depends_on = None


def upgrade():
    # Add cost tracking fields
    op.add_column('nodes', sa.Column('estimated_cost', sa.Float, nullable=True))
    op.add_column('nodes', sa.Column('actual_cost', sa.Float, nullable=True))
    
    # Add warnings field (JSON array stored as text)
    op.add_column('nodes', sa.Column('warnings', sa.Text, nullable=True))


def downgrade():
    op.drop_column('nodes', 'warnings')
    op.drop_column('nodes', 'actual_cost')
    op.drop_column('nodes', 'estimated_cost')
