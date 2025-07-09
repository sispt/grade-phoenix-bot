"""
Add session_expired_notified column to users table
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('users', sa.Column('session_expired_notified', sa.Boolean(), nullable=False, server_default=sa.false()))

def downgrade():
    op.drop_column('users', 'session_expired_notified') 