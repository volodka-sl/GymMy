"""add subscription trigger

Revision ID: afc2c0b03818
Revises: 8f908b308e7f
Create Date: 2025-07-09 21:52:03.606864

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'afc2c0b03818'
down_revision = '8f908b308e7f'
branch_labels = None
depends_on = None


def upgrade():
    # создаём или заменяем функцию
    op.execute("""
    CREATE OR REPLACE FUNCTION create_subscription_reminders()
    RETURNS TRIGGER AS $$
    BEGIN
      -- напоминание за 3 дня
      INSERT INTO subscription_reminder(user_subscription_id, remind_at, type)
        VALUES (NEW.subscription_id, NEW.end_ts - INTERVAL '3 days', 'before_3d');
      -- напоминание в день окончания
      INSERT INTO subscription_reminder(user_subscription_id, remind_at, type)
        VALUES (NEW.subscription_id, NEW.end_ts, 'on_end');
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # пересоздаём триггер
    op.execute("DROP TRIGGER IF EXISTS trg_create_reminders ON user_subscription;")
    op.execute("""
    CREATE TRIGGER trg_create_reminders
      AFTER INSERT ON user_subscription
      FOR EACH ROW
      EXECUTE FUNCTION create_subscription_reminders();
    """)


def downgrade():
    # убираем триггер и функцию при откате
    op.execute("DROP TRIGGER IF EXISTS trg_create_reminders ON user_subscription;")
    op.execute("DROP FUNCTION IF EXISTS create_subscription_reminders();")
