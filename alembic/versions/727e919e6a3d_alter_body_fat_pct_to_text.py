"""Alter body_fat_pct to text

Revision ID: 727e919e6a3d
Revises: 74fe3a100f81
Create Date: 2025-07-08 01:27:33.873103

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '727e919e6a3d'
down_revision = '74fe3a100f81'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # только изменение типа поля
    op.alter_column(
        'user',
        'body_fat_pct',
        existing_type=sa.DECIMAL(5, 2),
        type_=sa.Text(),
        nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        'user',
        'body_fat_pct',
        existing_type=sa.Text(),
        type_=sa.DECIMAL(5, 2),
        nullable=True
    )
