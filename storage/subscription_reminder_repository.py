# storage/subscription_reminder_repository.py

from datetime import datetime
from sqlalchemy.orm import Session
from storage.db import SessionLocal
from storage.models import SubscriptionReminder

class SubscriptionReminderRepository:
    """
    CRUD-операции и выборки по напоминаниям об оплате подписки.
    """

    def __init__(self):
        self._session: Session = SessionLocal()

    def list_unsent_reminders(self, now_utc: datetime) -> list[SubscriptionReminder]:
        return (
            self._session
            .query(SubscriptionReminder)
            .filter(
                SubscriptionReminder.sent == False,
                SubscriptionReminder.remind_at <= now_utc
            )
            .all()
        )

    def mark_as_sent(self, reminder: SubscriptionReminder):
        """
        Отметить напоминание как отправленное.
        """
        reminder.sent = True
        reminder.sent_ts = datetime.utcnow()
        self._session.commit()

    def close(self):
        self._session.close()
