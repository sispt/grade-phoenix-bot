"""
Change telegram_id to BigInteger to support large Telegram IDs

Revision ID: 002
Revises: 001
Create Date: 2024-07-09 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # MySQL: ALTER COLUMN to BIGINT
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('telegram_id',
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False
        )

def downgrade() -> None:
    # Revert back to Integer
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('telegram_id',
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False
        ) 