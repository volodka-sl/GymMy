"""add promo_code tables

Revision ID: 5d6883e8d864
Revises: afc2c0b03818
Create Date: 2025-07-09 22:02:53.834085

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5d6883e8d864'
down_revision = 'afc2c0b03818'
branch_labels = None
depends_on = None


def upgrade():
    # создаём ENUM-тип
    op.execute("CREATE TYPE promo_code_type AS ENUM ('discount_percent','discount_fixed','free_days');")

    # таблица промокодов
    op.create_table(
        'promo_code',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('code', sa.Text, nullable=False, unique=True),
        sa.Column('type', sa.Enum('discount_percent','discount_fixed','free_days', name='promo_code_type'), nullable=False),
        sa.Column('discount_pct', sa.Numeric(5,2)),
        sa.Column('discount_amt', sa.Numeric(10,2)),
        sa.Column('free_days', sa.Integer),
        sa.Column('valid_from', sa.Date, nullable=False, server_default=sa.text('CURRENT_DATE')),
        sa.Column('valid_to', sa.Date),
        sa.Column('usage_limit', sa.Integer),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('description', sa.Text),
    )

    # таблица использования
    op.create_table(
        'user_promo_code',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.BigInteger, nullable=False),
        sa.Column('promo_code_id', sa.Integer, nullable=False),
        sa.Column('redeemed_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['"user".user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['promo_code_id'], ['promo_code.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'promo_code_id', name='uq_user_promo'),
    )

def downgrade():
    op.drop_table('user_promo_code')
    op.drop_table('promo_code')
    op.execute("DROP TYPE promo_code_type;")
