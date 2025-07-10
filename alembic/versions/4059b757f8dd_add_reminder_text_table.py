"""add reminder_text table

Revision ID: 4059b757f8dd
Revises: 74094d6bb26e
Create Date: 2025-07-10 11:53:10.633640

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4059b757f8dd'
down_revision = '74094d6bb26e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'reminder_text',
        sa.Column('reminder_text_id', sa.Integer, primary_key=True),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('gender', sa.Enum('male', 'female', name='remindergender'), nullable=False),
        sa.Column('text', sa.Text, nullable=False),
        sa.UniqueConstraint('date', 'gender', name='uq_reminder_date_gender')
    )

def downgrade():
    op.drop_table('reminder_text')
    sa.Enum(name='remindergender').drop(op.get_bind())
