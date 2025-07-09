"""Initial migration - create users and grades tables

Revision ID: 001
Revises: 
Create Date: 2024-07-09 08:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('telegram_id', sa.Integer(), nullable=False),
        sa.Column('fullname', sa.String(length=200), nullable=True),
        sa.Column('firstname', sa.String(length=100), nullable=True),
        sa.Column('lastname', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('session_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('username'),
        sa.UniqueConstraint('telegram_id')
    )
    
    # Create grades table
    op.create_table('grades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('coursework', sa.String(length=50), nullable=True),
        sa.Column('final_exam', sa.String(length=50), nullable=True),
        sa.Column('total', sa.String(length=50), nullable=True),
        sa.Column('ects', sa.Float(), nullable=True),
        sa.Column('term_name', sa.String(length=200), nullable=True),
        sa.Column('term_id', sa.String(length=100), nullable=True),
        sa.Column('grade_status', sa.String(length=50), nullable=True),
        sa.Column('numeric_grade', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['username'], ['users.username'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index(op.f('ix_grades_username'), 'grades', ['username'], unique=False)
    op.create_index(op.f('ix_grades_code'), 'grades', ['code'], unique=False)
    op.create_index(op.f('ix_grades_term_name'), 'grades', ['term_name'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_grades_term_name'), table_name='grades')
    op.drop_index(op.f('ix_grades_code'), table_name='grades')
    op.drop_index(op.f('ix_grades_username'), table_name='grades')
    
    # Drop tables
    op.drop_table('grades')
    op.drop_table('users') 